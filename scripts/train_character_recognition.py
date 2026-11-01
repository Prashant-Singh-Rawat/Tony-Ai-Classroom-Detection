"""
scripts/train_character_recognition.py — Training & Evaluation Pipeline
======================================================================
Trains the lightweight CharacterCNN on the Kaggle English Character Recognition dataset.
Features:
- Stratified Train / Validation / Test splitting (70% / 15% / 15%) without data leakage.
- Image preprocessing and normalization (Grayscale 32x32, normalized [-1.0, 1.0]).
- Dynamic CUDA / CPU fallback detection.
- Comprehensive evaluation: Accuracy, Macro/Weighted Precision, Recall, F1-score, Confusion Matrix.
- Saves model checkpoints, class mappings, preprocessing configs, and performance metrics.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Add repository root to python search path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from backend.app.services.ocr.character_cnn import (
    CharacterCNN,
    build_class_mappings,
    class_name_to_character,
    get_default_class_names,
)


class CharacterDataset(Dataset):
    """PyTorch Dataset loading pre-indexed character images from disk."""

    def __init__(self, samples: List[Tuple[str, int]], transform=None) -> None:
        self.samples = samples
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]
        with Image.open(img_path) as img:
            img = img.convert("L")  # Convert to single-channel Grayscale
            if self.transform is not None:
                tensor_img = self.transform(img)
            else:
                tensor_img = transforms.ToTensor()(img)
        return tensor_img, label


def create_stratified_splits(
    dataset_dir: str,
    class_names: List[str],
    max_samples_per_class: int = 150,
    val_split: float = 0.15,
    test_split: float = 0.15,
    seed: int = 42,
) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]], List[Tuple[str, int]], Dict[str, Any]]:
    """
    Creates stratified Train, Validation, and Test splits.
    Guarantees no data leakage across splits.
    """
    rng = random.Random(seed)
    train_samples: List[Tuple[str, int]] = []
    val_samples: List[Tuple[str, int]] = []
    test_samples: List[Tuple[str, int]] = []

    per_class_summary = {}

    for cls_idx, cls_name in enumerate(class_names):
        cls_folder = os.path.join(dataset_dir, cls_name)
        if not os.path.isdir(cls_folder):
            raise FileNotFoundError(f"Class folder missing: {cls_folder}")

        all_files = sorted([f for f in os.listdir(cls_folder) if f.lower().endswith(".png")])
        if len(all_files) == 0:
            raise ValueError(f"No image files found in class folder: {cls_folder}")

        # Subsample if max_samples_per_class is specified > 0
        if 0 < max_samples_per_class < len(all_files):
            selected_files = rng.sample(all_files, max_samples_per_class)
        else:
            selected_files = list(all_files)

        rng.shuffle(selected_files)

        n_total = len(selected_files)
        n_val = int(n_total * val_split)
        n_test = int(n_total * test_split)
        n_train = n_total - n_val - n_test

        train_files = selected_files[:n_train]
        val_files = selected_files[n_train : n_train + n_val]
        test_files = selected_files[n_train + n_val :]

        train_samples.extend([(os.path.join(cls_folder, f), cls_idx) for f in train_files])
        val_samples.extend([(os.path.join(cls_folder, f), cls_idx) for f in val_files])
        test_samples.extend([(os.path.join(cls_folder, f), cls_idx) for f in test_files])

        per_class_summary[cls_name] = {
            "total_available": len(all_files),
            "sampled_total": n_total,
            "train": len(train_files),
            "val": len(val_files),
            "test": len(test_files),
        }

    # Shuffle combined sets
    rng.shuffle(train_samples)
    rng.shuffle(val_samples)
    rng.shuffle(test_samples)

    split_stats = {
        "seed": seed,
        "total_classes": len(class_names),
        "total_train": len(train_samples),
        "total_val": len(val_samples),
        "total_test": len(test_samples),
        "total_used": len(train_samples) + len(val_samples) + len(test_samples),
        "per_class": per_class_summary,
    }

    return train_samples, val_samples, test_samples, split_stats


def train_model(
    dataset_dir: str,
    output_dir: str,
    epochs: int = 6,
    batch_size: int = 64,
    learning_rate: float = 0.001,
    max_samples_per_class: int = 150,
    seed: int = 42,
) -> dict:
    start_time = time.time()
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)

    # 1. Device Selection & Hardware Profiling
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "HP Victus CPU Fallback"
    print(f"[*] Training Device: {device} ({device_name})")

    os.makedirs(output_dir, exist_ok=True)

    # 2. Class Names & Mappings
    class_names = sorted(os.listdir(dataset_dir))
    if len(class_names) != 62:
        class_names = get_default_class_names()
    class_mappings = build_class_mappings(class_names)

    # Save class mappings
    class_map_path = os.path.join(output_dir, "class_mapping.json")
    with open(class_map_path, "w", encoding="utf-8") as f:
        json.dump(class_mappings, f, indent=2)

    # 3. Create Dataset Splits (No Data Leakage)
    print(f"[*] Generating stratified splits from: {dataset_dir}")
    train_samples, val_samples, test_samples, split_stats = create_stratified_splits(
        dataset_dir=dataset_dir,
        class_names=class_names,
        max_samples_per_class=max_samples_per_class,
        val_split=0.15,
        test_split=0.15,
        seed=seed,
    )
    print(f"    Train: {len(train_samples)} | Val: {len(val_samples)} | Test: {len(test_samples)}")

    # 4. Data Preprocessing & Augmentation Pipelines
    train_transform = transforms.Compose([
        transforms.Resize((32, 32)),
        transforms.RandomRotation(degrees=8),
        transforms.RandomAffine(degrees=0, translate=(0.04, 0.04)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5]),
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((32, 32)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5]),
    ])

    preprocessing_config = {
        "input_resolution": [32, 32],
        "channels": 1,
        "color_space": "Grayscale",
        "normalization_mean": [0.5],
        "normalization_std": [0.5],
        "target_range": "[-1.0, 1.0]",
        "num_classes": len(class_names),
    }
    with open(os.path.join(output_dir, "preprocessing_config.json"), "w", encoding="utf-8") as f:
        json.dump(preprocessing_config, f, indent=2)

    # DataLoaders
    train_loader = DataLoader(
        CharacterDataset(train_samples, transform=train_transform),
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
    )
    val_loader = DataLoader(
        CharacterDataset(val_samples, transform=eval_transform),
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )
    test_loader = DataLoader(
        CharacterDataset(test_samples, transform=eval_transform),
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )

    # 5. Model Initialization
    model = CharacterCNN(num_classes=len(class_names)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=1)

    best_val_acc = 0.0
    best_checkpoint_path = os.path.join(output_dir, "best_character_cnn.pth")
    epoch_history = []

    print(f"[*] Starting model training ({epochs} epochs)...")

    # 6. Training Loop
    for epoch in range(1, epochs + 1):
        epoch_t0 = time.time()
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for inputs, targets in train_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * inputs.size(0)
            preds = outputs.argmax(dim=1)
            correct_train += (preds == targets).sum().item()
            total_train += targets.size(0)

        epoch_train_loss = running_loss / total_train
        epoch_train_acc = (correct_train / total_train) * 100.0

        # Validation Phase
        model.eval()
        val_loss = 0.0
        correct_val = 0
        total_val = 0

        with torch.no_grad():
            for inputs, targets in val_loader:
                inputs, targets = inputs.to(device), targets.to(device)
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                val_loss += loss.item() * inputs.size(0)
                preds = outputs.argmax(dim=1)
                correct_val += (preds == targets).sum().item()
                total_val += targets.size(0)

        epoch_val_loss = val_loss / total_val
        epoch_val_acc = (correct_val / total_val) * 100.0
        epoch_duration = time.time() - epoch_t0

        scheduler.step(epoch_val_acc)

        is_best = epoch_val_acc > best_val_acc
        if is_best:
            best_val_acc = epoch_val_acc
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_accuracy": best_val_acc,
                "val_loss": epoch_val_loss,
                "num_classes": len(class_names),
                "device": str(device),
            }, best_checkpoint_path)

        epoch_history.append({
            "epoch": epoch,
            "train_loss": round(epoch_train_loss, 4),
            "train_acc_pct": round(epoch_train_acc, 2),
            "val_loss": round(epoch_val_loss, 4),
            "val_acc_pct": round(epoch_val_acc, 2),
            "duration_seconds": round(epoch_duration, 2),
            "is_best": is_best,
        })

        star = " (*BEST*)" if is_best else ""
        print(f"  Epoch [{epoch}/{epochs}] ({epoch_duration:.1f}s) — Train Loss: {epoch_train_loss:.4f}, Train Acc: {epoch_train_acc:.2f}% | Val Loss: {epoch_val_loss:.4f}, Val Acc: {epoch_val_acc:.2f}%{star}")

    total_training_time = time.time() - start_time
    print(f"[*] Training finished in {total_training_time:.2f} seconds. Best Val Acc: {best_val_acc:.2f}%")

    # 7. Comprehensive Independent Test Set Evaluation
    print("[*] Evaluating best model on independent Test set...")
    checkpoint = torch.load(best_checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    all_preds = []
    all_targets = []
    all_top3_hits = 0
    inference_durations = []

    with torch.no_grad():
        for inputs, targets in test_loader:
            inputs, targets = inputs.to(device), targets.to(device)
            t_inf0 = time.perf_counter()
            outputs = model(inputs)
            t_inf1 = time.perf_counter()
            inference_durations.append((t_inf1 - t_inf0) / inputs.size(0))

            probs = torch.softmax(outputs, dim=1)
            preds = probs.argmax(dim=1)
            top3 = torch.topk(probs, k=3, dim=1).indices

            for t, p, topk in zip(targets.cpu().numpy(), preds.cpu().numpy(), top3.cpu().numpy()):
                all_targets.append(int(t))
                all_preds.append(int(p))
                if int(t) in topk:
                    all_top3_hits += 1

    all_targets = np.array(all_targets)
    all_preds = np.array(all_preds)

    test_accuracy = float(accuracy_score(all_targets, all_preds))
    top3_accuracy = float(all_top3_hits / len(all_targets))
    precision_macro = float(precision_score(all_targets, all_preds, average="macro", zero_division=0))
    precision_weighted = float(precision_score(all_targets, all_preds, average="weighted", zero_division=0))
    recall_macro = float(recall_score(all_targets, all_preds, average="macro", zero_division=0))
    recall_weighted = float(recall_score(all_targets, all_preds, average="weighted", zero_division=0))
    f1_macro = float(f1_score(all_targets, all_preds, average="macro", zero_division=0))
    f1_weighted = float(f1_score(all_targets, all_preds, average="weighted", zero_division=0))
    conf_mat = confusion_matrix(all_targets, all_preds).tolist()

    avg_inference_ms = float(np.mean(inference_durations) * 1000.0)

    evaluation_report = {
        "test_samples": len(all_targets),
        "test_accuracy": round(test_accuracy, 4),
        "top3_accuracy": round(top3_accuracy, 4),
        "precision_macro": round(precision_macro, 4),
        "precision_weighted": round(precision_weighted, 4),
        "recall_macro": round(recall_macro, 4),
        "recall_weighted": round(recall_weighted, 4),
        "f1_score_macro": round(f1_macro, 4),
        "f1_score_weighted": round(f1_weighted, 4),
        "avg_inference_latency_ms": round(avg_inference_ms, 2),
        "confusion_matrix_shape": [len(conf_mat), len(conf_mat[0])],
    }

    # Save metrics and evaluation outputs
    training_metrics_record = {
        "status": "COMPLETED",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hardware": {
            "device": str(device),
            "device_name": device_name,
            "cuda_available": torch.cuda.is_available(),
        },
        "hyperparameters": {
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "max_samples_per_class": max_samples_per_class,
            "optimizer": "Adam(lr=0.001, weight_decay=1e-4)",
            "scheduler": "ReduceLROnPlateau(factor=0.5, patience=1)",
            "loss_function": "CrossEntropyLoss",
        },
        "timing": {
            "total_training_seconds": round(total_training_time, 2),
            "best_epoch": checkpoint["epoch"],
        },
        "splits": split_stats,
        "epoch_history": epoch_history,
        "best_validation_accuracy": round(best_val_acc, 2),
        "test_evaluation": evaluation_report,
    }

    with open(os.path.join(output_dir, "training_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(training_metrics_record, f, indent=2)

    with open(os.path.join(output_dir, "evaluation_results.json"), "w", encoding="utf-8") as f:
        json.dump({
            "metrics": evaluation_report,
            "confusion_matrix": conf_mat,
        }, f, indent=2)

    print("=" * 70)
    print("CHARACTER RECOGNITION EVALUATION SUMMARY")
    print("=" * 70)
    print(f"  Test Accuracy:        {test_accuracy * 100:.2f}%")
    print(f"  Top-3 Accuracy:       {top3_accuracy * 100:.2f}%")
    print(f"  Macro Precision:      {precision_macro:.4f}")
    print(f"  Macro Recall:         {recall_macro:.4f}")
    print(f"  Macro F1-Score:       {f1_macro:.4f}")
    print(f"  Weighted F1-Score:    {f1_weighted:.4f}")
    print(f"  Avg Inference Latency:{avg_inference_ms:.2f} ms / sample")
    print(f"  Checkpoint Path:      {best_checkpoint_path}")
    print("=" * 70)

    return training_metrics_record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train English Character Recognition CNN")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=str(REPO_ROOT / "datasets" / "kaggle" / "handwriting" / "english_character_recognition"),
        help="Path to English Character Recognition dataset folder",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(REPO_ROOT / "models" / "checkpoints" / "character_recognition"),
        help="Directory to save checkpoint and configuration artifacts",
    )
    parser.add_argument("--epochs", type=int, default=6, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size for DataLoader")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument(
        "--max-samples-per-class",
        type=int,
        default=150,
        help="Maximum samples per class to sample for balanced training (e.g. 150*62=9,300 images)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")

    args = parser.parse_args()

    train_model(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        max_samples_per_class=args.max_samples_per_class,
        seed=args.seed,
    )

