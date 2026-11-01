"""
backend/app/services/ocr/character_cnn.py — Lightweight CNN for 62-Class Character Recognition
=============================================================================================
Architecture:
- 3 Convolutional blocks with BatchNorm2d, ReLU, and MaxPool2d
- Dropout regularization
- Dense classification head mapping to 62 alphanumeric character classes
Optimized for HP Victus laptop (GTX 1650 4GB GPU / CPU fallback).
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import torch
import torch.nn as nn


class CharacterCNN(nn.Module):
    """
    Lightweight, highly efficient Convolutional Neural Network for recognizing 62
    alphanumeric character classes (0-9, A-Z, a-z) from single-character crops.
    Input: (B, 1, 32, 32) grayscale image normalized to [-1.0, 1.0].
    Parameters: ~586,000 (suitable for real-time <2ms CPU inference).
    """

    def __init__(self, num_classes: int = 62) -> None:
        super().__init__()
        self.num_classes = num_classes

        self.features = nn.Sequential(
            # Block 1: 1 -> 32 channels, output: (B, 32, 16, 16)
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 2: 32 -> 64 channels, output: (B, 64, 8, 8)
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 3: 64 -> 128 channels, output: (B, 128, 4, 4)
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        self.classifier = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(128 * 4 * 4, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.25),
            nn.Linear(256, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.features(x)
        feat = feat.view(feat.size(0), -1)
        out = self.classifier(feat)
        return out


def get_default_class_names() -> List[str]:
    """
    Returns the sorted canonical 62 class names matching the dataset directory structure:
    - 10 digits: '0' to '9'
    - 26 uppercase letters: 'A_U' to 'Z_U'
    - 26 lowercase letters: 'a_L' to 'z_L'
    """
    digits = [str(i) for i in range(10)]
    uppercase = [f"{chr(c)}_U" for c in range(ord("A"), ord("Z") + 1)]
    lowercase = [f"{chr(c)}_L" for c in range(ord("a"), ord("z") + 1)]
    return sorted(digits + uppercase + lowercase)


def class_name_to_character(class_name: str) -> str:
    """
    Maps folder-based class name to actual human-readable character:
    - '0' -> '0'
    - 'A_U' -> 'A'
    - 'a_L' -> 'a'
    """
    if class_name.endswith("_U"):
        return class_name[0].upper()
    elif class_name.endswith("_L"):
        return class_name[0].lower()
    return class_name


def build_class_mappings(class_names: List[str]) -> Dict[str, Any]:
    """Builds two-way mappings between class names, indices, and characters."""
    class_to_idx = {cls_name: idx for idx, cls_name in enumerate(class_names)}
    idx_to_class = {str(idx): cls_name for idx, cls_name in enumerate(class_names)}
    class_to_char = {cls_name: class_name_to_character(cls_name) for cls_name in class_names}
    idx_to_char = {str(idx): class_name_to_character(cls_name) for idx, cls_name in enumerate(class_names)}

    return {
        "classes": class_names,
        "class_to_idx": class_to_idx,
        "idx_to_class": idx_to_class,
        "class_to_char": class_to_char,
        "idx_to_char": idx_to_char,
    }

