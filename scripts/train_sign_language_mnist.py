"""
scripts/train_sign_language_mnist.py — Train Lightweight Sign Language CNN
===========================================================================
Trains a lightweight 2-block CNN on Sign Language MNIST (24 ASL Alphabet Classes).
Evaluates on the official untouched test set (7,172 samples).
Computes Accuracy, Precision, Recall, F1-Score, and 24x24 Confusion Matrix.
Saves checkpoint to models/checkpoints/sign_language/best_sign_language_cnn.pth.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import StratifiedShuffleSplit
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "datasets" / "kaggle" / "sign_language_mnist"
CHECKPOINT_DIR = REPO_ROOT / "models" / "checkpoints" / "sign_language"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)


# ---------------------------------------------------------------------------
# Dataset Definition
# ---------------------------------------------------------------------------
class SignLanguageDataset(Dataset):
    def __init__(self, df: pd.DataFrame, label_to_idx: dict[int, int], transform=None):
        self.labels = [label_to_idx[l] for l in df["label"].values]
        # Pixel values columns: pixel1 to pixel784 (28x28)
        pixel_cols = [c for c in df.columns if c.startswith("pixel")]
        self.pixels = df[pixel_cols].values.astype(np.float32) / 255.0  # Normalize to [0, 1]
        self.transform = transform

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        img_array = self.pixels[idx].reshape(28, 28)
        tensor = torch.from_numpy(img_array).unsqueeze(0)  # Shape: (1, 28, 28)
        # Normalize to [-1, 1]
        tensor = (tensor - 0.5) / 0.5
        label = self.labels[idx]
        return tensor, label


# ---------------------------------------------------------------------------
# Model Architecture
# ---------------------------------------------------------------------------
class SignLanguageCNN(nn.Module):
    def __init__(self, num_classes: int = 24):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1: 1 -> 32
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),  # -> 14x14
            nn.Dropout2d(0.1),

            # Block 2: 32 -> 64
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),  # -> 7x7
            nn.Dropout2d(0.2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return self.classifier(x)


# ---------------------------------------------------------------------------
# Training & Evaluation Loop
# ---------------------------------------------------------------------------
def main():
    train_csv = DATA_DIR / "sign_mnist_train.csv"
    test_csv = DATA_DIR / "sign_mnist_test.csv"

    if not train_csv.is_file() or not test_csv.is_file():
        logger.error("Sign Language MNIST CSVs not found in %s", DATA_DIR)
        return

    logger.info("Loading Sign Language MNIST data...")
    df_train_full = pd.read_csv(train_csv)
    df_test = pd.read_csv(test_csv)

    # Class mappings
    raw_classes = sorted(df_train_full["label"].unique().tolist())
    label_to_idx = {raw_cls: idx for idx, raw_cls in enumerate(raw_classes)}
    idx_to_label = {idx: raw_cls for raw_cls, idx in label_to_idx.items()}
    num_classes = len(raw_classes)

    # Map numerical label to English letter: 0='A', 1='B', ..., 25='Z' (excluding 9='J' and 25='Z')
    idx_to_letter = {idx: chr(ord('A') + raw_cls) for idx, raw_cls in idx_to_label.items()}
    logger.info("Classes (%d): %s", num_classes, [f"{raw}->{idx_to_letter[idx]}" for raw, idx in label_to_idx.items()])

    # Stratified Train/Val Split (80/20 of train set)
    sss = StratifiedShuffleSplit(n_splits=1, test_size=0.20, random_state=SEED)
    train_idx, val_idx = next(sss.split(df_train_full, df_train_full["label"].values))

    df_train = df_train_full.iloc[train_idx].reset_index(drop=True)
    df_val = df_train_full.iloc[val_idx].reset_index(drop=True)

    train_dataset = SignLanguageDataset(df_train, label_to_idx)
    val_dataset = SignLanguageDataset(df_val, label_to_idx)
    test_dataset = SignLanguageDataset(df_test, label_to_idx)

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Hardware profiling: using %s", device)

    model = SignLanguageCNN(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=1)

    epochs = 5
    best_val_acc = 0.0
    best_checkpoint = CHECKPOINT_DIR / "best_sign_language_cnn.pth"

    start_time = time.perf_counter()
    logger.info("Starting training for %d epochs...", epochs)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss, correct, total = 0.0, 0, 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * len(labels)
            preds = outputs.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += len(labels)

        train_loss = total_loss / total
        train_acc = correct / total

        # Validation
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                preds = outputs.argmax(dim=1)
                val_correct += (preds == labels).sum().item()
                val_total += len(labels)

        val_acc = val_correct / val_total
        scheduler.step(val_acc)

        logger.info(
            "Epoch %d/%d — Train Loss: %.4f | Train Acc: %.2f%% | Val Acc: %.2f%%",
            epoch, epochs, train_loss, train_acc * 100.0, val_acc * 100.0
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "val_acc": val_acc,
                    "num_classes": num_classes,
                },
                best_checkpoint,
            )

    train_duration = time.perf_counter() - start_time
    logger.info("Training completed in %.2f seconds. Best Val Acc: %.2f%%", train_duration, best_val_acc * 100.0)

    # -----------------------------------------------------------------------
    # Comprehensive Test Evaluation
    # -----------------------------------------------------------------------
    logger.info("Loading best checkpoint for held-out test evaluation...")
    checkpoint = torch.load(best_checkpoint, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    all_preds = []
    all_targets = []
    all_top3 = []
    latency_records = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            t0 = time.perf_counter()
            outputs = model(images)
            t1 = time.perf_counter()
            latency_records.append((t1 - t0) / len(labels))

            probs = F.softmax(outputs, dim=1)
            top1 = outputs.argmax(dim=1).cpu().numpy()
            top3 = torch.topk(probs, k=3, dim=1).indices.cpu().numpy()

            all_preds.extend(top1)
            all_targets.extend(labels.numpy())
            for true_l, t3 in zip(labels.numpy(), top3):
                all_top3.append(true_l in t3)

    all_preds = np.array(all_preds)
    all_targets = np.array(all_targets)

    test_acc = float((all_preds == all_targets).mean())
    top3_acc = float(np.mean(all_top3))
    prec_macro = float(precision_score(all_targets, all_preds, average="macro", zero_division=0))
    prec_weighted = float(precision_score(all_targets, all_preds, average="weighted", zero_division=0))
    rec_macro = float(recall_score(all_targets, all_preds, average="macro", zero_division=0))
    rec_weighted = float(recall_score(all_targets, all_preds, average="weighted", zero_division=0))
    f1_macro = float(f1_score(all_targets, all_preds, average="macro", zero_division=0))
    f1_weighted = float(f1_score(all_targets, all_preds, average="weighted", zero_division=0))
    avg_latency_ms = round(float(np.mean(latency_records) * 1000.0), 3)

    cm = confusion_matrix(all_targets, all_preds).tolist()

    logger.info("================ TEST EVALUATION RESULTS ================")
    logger.info("Test Samples: %d", len(all_targets))
    logger.info("Top-1 Test Accuracy: %.2f%%", test_acc * 100.0)
    logger.info("Top-3 Test Accuracy: %.2f%%", top3_acc * 100.0)
    logger.info("Macro Precision: %.4f | Weighted Precision: %.4f", prec_macro, prec_weighted)
    logger.info("Macro Recall:    %.4f | Weighted Recall:    %.4f", rec_macro, rec_weighted)
    logger.info("Macro F1-Score:  %.4f | Weighted F1-Score:  %.4f", f1_macro, f1_weighted)
    logger.info("Avg CPU Latency: %.3f ms / sample", avg_latency_ms)

    # Save artifacts
    mapping_payload = {
        "raw_classes": raw_classes,
        "label_to_idx": label_to_idx,
        "idx_to_label": idx_to_label,
        "idx_to_letter": idx_to_letter,
        "class_letters": [idx_to_letter[i] for i in range(num_classes)],
    }
    with open(CHECKPOINT_DIR / "class_mapping.json", "w", encoding="utf-8") as f:
        json.dump(mapping_payload, f, indent=2)

    eval_results = {
        "dataset": "Sign Language MNIST",
        "num_classes": num_classes,
        "test_samples": len(all_targets),
        "test_accuracy": round(test_acc, 4),
        "top3_accuracy": round(top3_acc, 4),
        "precision_macro": round(prec_macro, 4),
        "precision_weighted": round(prec_weighted, 4),
        "recall_macro": round(rec_macro, 4),
        "recall_weighted": round(rec_weighted, 4),
        "f1_score_macro": round(f1_macro, 4),
        "f1_score_weighted": round(f1_weighted, 4),
        "avg_inference_latency_ms": avg_latency_ms,
        "training_time_seconds": round(train_duration, 2),
        "device": str(device),
        "model_architecture": "SignLanguageCNN (2 Conv blocks, 1 Dense block, ~150k params)",
        "confusion_matrix": cm,
    }
    with open(CHECKPOINT_DIR / "evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2)

    print("Sign Language MNIST model training and evaluation successfully completed!")


if __name__ == "__main__":
    main()

