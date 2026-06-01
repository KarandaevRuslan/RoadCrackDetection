"""Console reporting for dataset builds."""

from __future__ import annotations

from pathlib import Path

from .stats import count_class_stats_from_labels, print_class_stats


def print_build_summary(
    source_root: Path,
    output_dir: Path,
    classes: list[str],
    train_count: int,
    val_count: int,
    test_count: int,
) -> None:
    """Print a short summary of the generated dataset."""
    print("OK: dataset built")
    print(f"Source root: {source_root}")
    print(f"Output directory: {output_dir}")
    print(f"Classes: {len(classes)} -> {classes}")
    print(f"Train images: {train_count}")
    print(f"Validation images: {val_count}")
    print(f"Test images: {test_count}")
    print(f"data.yaml: {output_dir / 'data.yaml'}")


def print_dataset_statistics(
    output_dir: Path,
    classes: list[str],
    include_test: bool,
) -> None:
    """Print per-class statistics for dataset splits."""
    split_names = ["train", "val"]

    if include_test:
        split_names.append("test")

    for split_name in split_names:
        label_paths = list((output_dir / "labels" / split_name).glob("*.txt"))

        images_per_class, instances_per_class, total_images, total_instances = (
            count_class_stats_from_labels(label_paths)
        )

        print_class_stats(
            title=f"{split_name.upper()} split stats:",
            classes=classes,
            images_per_class=images_per_class,
            instances_per_class=instances_per_class,
            total_images=total_images,
            total_instances=total_instances,
        )
