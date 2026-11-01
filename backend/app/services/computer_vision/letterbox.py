"""
backend/app/services/computer_vision/letterbox.py
=================================================
Aspect-Ratio Preserving Preprocessing & Letterboxing Utilities.
Guarantees frames are NEVER stretched or distorted to fit model input dimensions.
"""

from __future__ import annotations

import math
from typing import Tuple, Optional
import cv2
import numpy as np


def compute_aspect_ratio_string(width: int, height: int) -> str:
    """Computes standard aspect ratio label for common video formats."""
    if width <= 0 or height <= 0:
        return "UNKNOWN"
    
    # Calculate float ratio
    ratio = width / height
    
    # Check standard landscape ratios
    if math.isclose(ratio, 16 / 9, rel_tol=0.03):
        return "16:9"
    elif math.isclose(ratio, 4 / 3, rel_tol=0.03):
        return "4:3"
    elif math.isclose(ratio, 21 / 9, rel_tol=0.04):
        return "21:9"
    elif math.isclose(ratio, 16 / 10, rel_tol=0.03):
        return "16:10"
    elif math.isclose(ratio, 1.0, rel_tol=0.03):
        return "1:1"
    # Check standard portrait ratios
    elif math.isclose(ratio, 9 / 16, rel_tol=0.03):
        return "9:16"
    elif math.isclose(ratio, 3 / 4, rel_tol=0.03):
        return "3:4"
    elif math.isclose(ratio, 10 / 16, rel_tol=0.03):
        return "10:16"
    else:
        # Reduced fraction approximation using gcd
        g = math.gcd(width, height)
        num, den = width // g, height // g
        if num > 30 or den > 30:
            return f"{round(ratio, 2)}:1"
        return f"{num}:{den}"


def letterbox_image(
    image: np.ndarray,
    target_shape: Tuple[int, int] = (640, 640),
    color: Tuple[int, int, int] = (114, 114, 114),
    stride: int = 32,
    auto: bool = True,
    scaleup: bool = True,
) -> Tuple[np.ndarray, float, Tuple[float, float]]:
    """
    Resizes image while strictly preserving aspect ratio and adds letterbox borders.
    Never stretches frames to fit target dimensions.

    Args:
        image: Original BGR image (H, W, 3).
        target_shape: Destination (target_h, target_w).
        color: Padding fill color in BGR (default: neutral grey 114).
        stride: Multiple constraint for convolutional downsampling strides.
        auto: If True, uses minimum rectangular padding conforming to stride.
        scaleup: If True, allows upscaling smaller frames; if False, only downsizes.

    Returns:
        padded_image: np.ndarray letterboxed image.
        ratio: float scaling factor applied to original image.
        (pad_w, pad_h): padding in pixels on left/right and top/bottom.
    """
    shape = image.shape[:2]  # [current_h, current_w]
    if isinstance(target_shape, int):
        target_shape = (target_shape, target_shape)

    # Scale ratio (new / old)
    r = min(target_shape[0] / shape[0], target_shape[1] / shape[1])
    if not scaleup:
        r = min(r, 1.0)

    # Compute unpadded dimensions
    new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
    dw = target_shape[1] - new_unpad[0]  # width padding
    dh = target_shape[0] - new_unpad[1]  # height padding

    if auto:  # Minimum rectangle padding conforming to stride
        dw = np.mod(dw, stride)
        dh = np.mod(dh, stride)

    dw /= 2.0  # Divide padding equally between sides
    dh /= 2.0

    # Resize strictly with uniform aspect ratio
    if shape[::-1] != new_unpad:
        interp = cv2.INTER_AREA if r < 1.0 else cv2.INTER_LINEAR
        image = cv2.resize(image, new_unpad, interpolation=interp)

    # Add letterbox border
    top = int(round(dh - 0.1))
    bottom = int(round(dh + 0.1))
    left = int(round(dw - 0.1))
    right = int(round(dw + 0.1))
    
    padded_image = cv2.copyMakeBorder(
        image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
    )
    return padded_image, r, (dw, dh)


def scale_boxes_to_original(
    boxes: np.ndarray,
    scale_ratio: float,
    padding: Tuple[float, float],
    original_shape: Tuple[int, int],
) -> np.ndarray:
    """
    Maps bounding boxes [x1, y1, x2, y2] from letterboxed image back to original dimensions.
    """
    if len(boxes) == 0:
        return boxes

    unpad_boxes = boxes.copy()
    pad_w, pad_h = padding
    orig_h, orig_w = original_shape

    # Subtract padding
    unpad_boxes[:, [0, 2]] -= pad_w
    unpad_boxes[:, [1, 3]] -= pad_h

    # Divide by uniform scale ratio
    unpad_boxes[:, :4] /= max(1e-6, scale_ratio)

    # Clip to original image boundaries
    unpad_boxes[:, [0, 2]] = np.clip(unpad_boxes[:, [0, 2]], 0, orig_w)
    unpad_boxes[:, [1, 3]] = np.clip(unpad_boxes[:, [1, 3]], 0, orig_h)
    return unpad_boxes


def scale_keypoints_to_original(
    keypoints: np.ndarray,
    scale_ratio: float,
    padding: Tuple[float, float],
    original_shape: Tuple[int, int],
) -> np.ndarray:
    """
    Maps keypoints [x, y, conf] from letterboxed image back to original dimensions.
    Supports 2D (num_kpts, 3) or 3D (num_persons, num_kpts, 3) arrays.
    """
    if len(keypoints) == 0:
        return keypoints

    unpad_kps = keypoints.copy()
    pad_w, pad_h = padding
    orig_h, orig_w = original_shape

    if unpad_kps.ndim == 2:
        # Subtract padding for x, y
        unpad_kps[:, 0] -= pad_w
        unpad_kps[:, 1] -= pad_h

        # Divide by scale ratio
        unpad_kps[:, :2] /= max(1e-6, scale_ratio)

        # Clip x, y to original image boundaries
        unpad_kps[:, 0] = np.clip(unpad_kps[:, 0], 0, orig_w)
        unpad_kps[:, 1] = np.clip(unpad_kps[:, 1], 0, orig_h)
    elif unpad_kps.ndim == 3:
        # Subtract padding for x, y
        unpad_kps[:, :, 0] -= pad_w
        unpad_kps[:, :, 1] -= pad_h

        # Divide by scale ratio
        unpad_kps[:, :, :2] /= max(1e-6, scale_ratio)

        # Clip x, y to original image boundaries
        unpad_kps[:, :, 0] = np.clip(unpad_kps[:, :, 0], 0, orig_w)
        unpad_kps[:, :, 1] = np.clip(unpad_kps[:, :, 1], 0, orig_h)

    return unpad_kps
