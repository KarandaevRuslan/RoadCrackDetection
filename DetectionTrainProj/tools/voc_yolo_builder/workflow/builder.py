"""Main dataset build workflow."""

from __future__ import annotations

import random

from ..dataset.class_filter import filter_classes_and_pairs
from ..dataset.writer import write_dataset_files
from ..dataset.discovery import discover_source_pairs
from ..domain.models import BuildConfig
from ..reporting.console import print_build_summary, print_dataset_statistics
from ..dataset.sampling import select_output_pairs
from ..dataset.splits import split_train_val_test


def build_class_index(classes: list[str]) -> dict[str, int]:
    """Build a stable class-name to class-id mapping."""
    return {
        class_name: class_id
        for class_id, class_name in enumerate(classes)
    }


def build_dataset(config: BuildConfig) -> None:
    """Build a YOLO dataset from Pascal VOC XML annotations."""
    config.output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(config.random_seed)

    pairs = discover_source_pairs(config.source_root)

    class_filter_result = filter_classes_and_pairs(
        pairs=pairs,
        min_source_images_per_class=config.min_source_images_per_class,
    )

    class_to_id = build_class_index(class_filter_result.classes)

    selected_pairs = select_output_pairs(
        pairs=class_filter_result.pairs,
        class_to_id=class_to_id,
        rng=rng,
        sample_fraction=config.sample_fraction,
        max_output_images=config.max_output_images,
        sampling_strategy=config.sampling_strategy,
        random_seed=config.random_seed,
        target_min_images_per_class=config.target_min_images_per_class,
    )

    train_pairs, val_pairs, test_pairs = split_train_val_test(
        selected_pairs,
        validation_ratio=config.validation_ratio,
        test_ratio=config.test_ratio,
    )

    write_dataset_files(
        output_dir=config.output_dir,
        train_pairs=train_pairs,
        val_pairs=val_pairs,
        test_pairs=test_pairs,
        class_to_id=class_to_id,
        classes=class_filter_result.classes,
        use_hardlinks=config.use_hardlinks,
    )

    print_build_summary(
        source_root=config.source_root,
        output_dir=config.output_dir,
        classes=class_filter_result.classes,
        train_count=len(train_pairs),
        val_count=len(val_pairs),
        test_count=len(test_pairs),
    )

    print_dataset_statistics(
        output_dir=config.output_dir,
        classes=class_filter_result.classes,
        include_test=bool(test_pairs),
    )
