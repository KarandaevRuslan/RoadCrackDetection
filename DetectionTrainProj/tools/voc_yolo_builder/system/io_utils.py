"""Filesystem and small value-conversion helpers."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple


def to_float(text: Optional[str]) -> Optional[float]:
    """Convert text to float, accepting both decimal dots and commas."""
    if text is None:
        return None

    value = text.strip()
    if not value:
        return None

    return float(value.replace(",", "."))


def clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamp a numeric value to the inclusive [low, high] interval."""
    return min(max(value, low), high)


def try_hardlink(src: Path, dst: Path) -> bool:
    """Try to create a hard link. Return True if it exists or was created."""
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            return True
        os.link(src, dst)
        return True
    except OSError:
        return False


def copy_or_link(src: Path, dst: Path, use_hardlink: bool) -> None:
    """Copy a file, optionally trying a hard link first."""
    if use_hardlink and try_hardlink(src, dst):
        return

    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def read_image_size_with_pillow(image_path: Path) -> Tuple[int, int]:
    """Read image dimensions with Pillow when XML size metadata is unusable."""
    try:
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            "Install Pillow to read image dimensions when XML <size> is missing "
            "or invalid: pip install pillow"
        ) from exc

    with Image.open(image_path) as image:
        width, height = image.size

    return int(width), int(height)


def ensure_dataset_dirs(output_dir: Path, include_test: bool = False) -> None:
    """Create YOLO dataset output directories."""
    split_names = ["train", "val"]

    if include_test:
        split_names.append("test")

    for split_name in split_names:
        (output_dir / "images" / split_name).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split_name).mkdir(parents=True, exist_ok=True)
