"""
scripts/train_hand_gesture.py — Train Lightweight 20-Class Hand Gesture CNN
===========================================================================
Trains a lightweight 2-block CNN on Kaggle Hand Gesture Recognition (20 classes: 0-19).
Evaluates on untouched test set with Accuracy, Precision, Recall, F1, and 20x20 Confusion Matrix.
Saves checkpoint to models/checkpoints/hand_gesture/best_gesture_cnn.pth.
Enforces strict boundary: numerical classes only; unmapped to classroom hand-raising.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
import numpy as np
from PIL import Image
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "datasets" / "kaggle" / "hand_gesture" / "extracted"
CHECKPOINT_DIR = REPO_ROOT / "models" / "checkpoints" / "hand_gesture"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)


class HandGestureImageDataset(Dataset):
    def __init__(self, file_paths: list[Path], labels: list[int], transform=None):
        self.file_paths = file_paths
        self.labels = labels
        self.transform = transform

    def __len__(self):
        return len(self.file_paths)

    def __getitem__(self, idx):
        path = self.file_paths[idx]
        with Image.open(path) as img:
            img = img.convert("L")  # 50x50 grayscale
            if self.transform:
                tensor = self.transform(img)
            else:
                tensor = transforms.ToTensor()(img)
                tensor = (tensor - 0.5) / 0.5
        label = self.labels[idx]
        return tensor, label


class HandGestureCNN(nn.Module):
    def __init__(self, num_classes: int = 20):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1: 1 -> 32 (50x50 -> 25x25)
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.1),

            # Block 2: 32 -> 64 (25x25 -> 12x12)
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 12 * 12, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.features(x)
        return self.classifier(x)


def main():
    train_dir = DATA_DIR / "train"
    test_dir = DATA_DIR / "test"

    if not train_dir.is_dir() or not test_dir.is_dir():
        logger.error("Hand gesture train/test directories not found in %s", DATA_DIR)
        return

    classes = sorted([d.name for d in train_dir.iterdir() if d.is_dir()], key=lambda x: int(x) if x.isdigit() else x)
    num_classes = len(classes)
    label_to_idx = {c: idx for idx, c in enumerate(classes)}

    logger.info("Found %d classes in hand gesture dataset: %s", num_classes, classes)

    # Subsample 200 images per class for training/val to enable fast CPU training
    train_paths, train_labels = [], []
    val_paths, val_labels = [], []
    test_paths, test_labels = [], []

    np.random.seed(SEED)
    for c in classes:
        c_train_files = sorted(list((train_dir / c).glob("*.jpg")))
        np.random.shuffle(c_train_files)
        # Use 160 for train, 40 for val (80/20 per class)
        c_train = c_train_files[:160]
        c_val = c_train_files[160:200]

        train_paths.extend(c_train)
        train_labels.extend([label_to_idx[c]] * len(c_train))
        val_paths.extend(c_val)
        val_labels.extend([label_to_idx[c]] * len(c_val))

        # Use 100 images per class for test evaluation
        c_test_files = sorted(list((test_dir / c).glob("*.jpg")))[:100]
        test_paths.extend(c_test_files)
        test_labels.extend([label_to_idx[c]] * len(c_test_files))

    logger.info("Samples — Train: %d, Val: %d, Test: %d", len(train_paths), len(val_paths), len(test_paths))

    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5], std=[0.5]),
    ])

    train_dataset = HandGestureImageDataset(train_paths, train_labels, transform=transform)
    val_dataset = HandGestureImageDataset(val_paths, val_labels, transform=transform)
    test_dataset = HandGestureImageDataset(test_paths, test_labels, transform=transform)

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Hardware profiling: using %s", device)

    model = HandGestureCNN(num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)

    epochs = 5
    best_val_acc = 0.0
    best_checkpoint = CHECKPOINT_DIR / "best_gesture_cnn.pth"

    start_time = time.perf_counter()
    logger.info("Training HandGestureCNN for %d epochs...", epochs)

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
        logger.info("Epoch %d/%d — Train Loss: %.4f | Train Acc: %.2f%% | Val Acc: %.2f%%",
                    epoch, epochs, train_loss, train_acc * 100.0, val_acc * 100.0)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_acc": val_acc,
                "num_classes": num_classes,
                "classes": classes,
            }, best_checkpoint)

    train_duration = time.perf_counter() - start_time
    logger.info("Training finished in %.2f seconds. Best Val Acc: %.2f%%", train_duration, best_val_acc * 100.0)

    # Held-out Test evaluation
    logger.info("Evaluating on held-out test split (%d samples)...", len(test_paths))
    checkpoint = torch.load(best_checkpoint, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    all_preds, all_targets, all_top3, latencies = [], [], [], []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            t0 = time.perf_counter()
            outputs = model(images)
            t1 = time.perf_counter()
            latencies.append((t1 - t0) / len(labels))

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
    avg_latency_ms = round(float(np.mean(latencies) * 1000.0), 3)

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
        "classes": classes,
        "label_to_idx": label_to_idx,
        "num_classes": num_classes,
        "semantic_status": "NUMERICAL_GESTURES_ONLY_UNMAPPED_TO_CLASSROOM",
    }
    with open(CHECKPOINT_DIR / "class_mapping.json", "w", encoding="utf-8") as f:
        json.dump(mapping_payload, f, indent=2)

    eval_results = {
        "dataset": "Kaggle Hand Gesture Recognition (20 classes: 0-19)",
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
        "model_architecture": "HandGestureCNN (2 Conv blocks, 1 Dense block, ~120k params)",
        "confusion_matrix": cm,
        "ethical_boundary": "Isolated numerical gesture classes; strictly NOT treated as classroom hand-raising ground truth",
    }
    with open(CHECKPOINT_DIR / "evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(eval_results, f, indent=2)

    print("Hand Gesture CNN training and evaluation successfully completed!")


if __name__ == "__main__":
    main()

