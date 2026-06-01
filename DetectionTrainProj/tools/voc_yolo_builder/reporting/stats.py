"""YOLO label statistics."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable, List, Tuple

from .tables import print_table


def count_class_stats_from_labels(
    label_paths: Iterable[Path],
) -> Tuple[Counter, Counter, int, int]:
    """Count image-level and instance-level class statistics from label files."""
    instances_per_class = Counter()
    images_per_class = Counter()
    total_images = 0
    total_instances = 0

    for label_path in label_paths:
        total_images += 1
        if not label_path.exists():
            continue

        text = label_path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        seen_in_image = set()
        for line in text.splitlines():
            parts = line.strip().split()
            if not parts:
                continue

            class_id = int(parts[0])
            instances_per_class[class_id] += 1
            total_instances += 1
            seen_in_image.add(class_id)

        for class_id in seen_in_image:
            images_per_class[class_id] += 1

    return images_per_class, instances_per_class, total_images, total_instances


def print_class_stats(
    title: str,
    classes: List[str],
    images_per_class: Counter,
    instances_per_class: Counter,
    total_images: int,
    total_instances: int,
) -> None:
    """Print class distribution statistics."""
    print()
    print(title)
    print(f"Number of classes: {len(classes)}")
    print(f"Total images: {total_images}")
    print(f"Total instances: {total_instances}")
    print()

    header = ["id", "class", "images", "images_norm", "instances", "inst_norm"]
    rows = []

    for class_id, class_name in enumerate(classes):
        image_count = int(images_per_class.get(class_id, 0))
        instance_count = int(instances_per_class.get(class_id, 0))
        image_norm = image_count / total_images if total_images > 0 else 0.0
        instance_norm = (
            instance_count / total_instances if total_instances > 0 else 0.0
        )

        rows.append(
            [
                class_id,
                class_name,
                image_count,
                f"{image_norm:.4f}",
                instance_count,
                f"{instance_norm:.4f}",
            ]
        )

    print_table(header, rows)
