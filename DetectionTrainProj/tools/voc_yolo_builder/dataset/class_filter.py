"""Class filtering utilities for source VOC annotations."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from ..domain.models import ImageAnnotationPair
from ..voc.parser import parse_voc_xml


@dataclass(frozen=True)
class ImageClassInfo:
    """Classes found in one source image."""

    pair: ImageAnnotationPair
    has_objects: bool
    class_names: set[str]


@dataclass(frozen=True)
class ClassFilterResult:
    """Result of source class filtering."""

    pairs: list[ImageAnnotationPair]
    classes: list[str]


def compute_global_class_image_counts(
    pairs: list[ImageAnnotationPair],
) -> tuple[list[ImageClassInfo], Counter[str]]:
    """Count how many source images contain each class at least once."""
    class_image_counts: Counter[str] = Counter()
    image_class_info: list[ImageClassInfo] = []

    for pair in pairs:
        _, _, objects = parse_voc_xml(pair.xml_path)

        class_names = {
            obj.class_name
            for obj in objects
            if obj.class_name
        }

        image_class_info.append(
            ImageClassInfo(
                pair=pair,
                has_objects=bool(objects),
                class_names=class_names,
            )
        )

        for class_name in class_names:
            class_image_counts[class_name] += 1

    return image_class_info, class_image_counts


def split_classes_by_min_image_count(
    class_image_counts: Counter[str],
    min_source_images_per_class: int,
) -> tuple[list[str], list[str]]:
    """Split classes into kept and dropped groups by source image count."""
    threshold = max(1, int(min_source_images_per_class))

    kept_classes = sorted(
        class_name
        for class_name, count in class_image_counts.items()
        if count >= threshold
    )
    dropped_classes = sorted(
        class_name
        for class_name, count in class_image_counts.items()
        if count < threshold
    )

    return kept_classes, dropped_classes


def filter_pairs_by_kept_classes(
    image_class_info: list[ImageClassInfo],
    kept_classes: set[str],
) -> list[ImageAnnotationPair]:
    """Keep negative images and images containing at least one kept class."""
    kept_with_objects = 0
    kept_without_objects = 0
    dropped_only_dropped_classes = 0

    filtered_pairs: list[ImageAnnotationPair] = []

    for item in image_class_info:
        if not item.has_objects:
            kept_without_objects += 1
            filtered_pairs.append(item.pair)
            continue

        if item.class_names & kept_classes:
            kept_with_objects += 1
            filtered_pairs.append(item.pair)
        else:
            dropped_only_dropped_classes += 1

    print("Filter results:")
    print(f"  kept_with_objects: {kept_with_objects}")
    print(f"  kept_without_objects: {kept_without_objects}")
    print(f"  dropped_only_dropped_classes: {dropped_only_dropped_classes}")

    return filtered_pairs


def filter_classes_and_pairs(
    pairs: list[ImageAnnotationPair],
    min_source_images_per_class: int,
) -> ClassFilterResult:
    """Drop rare classes and remove images that only contain dropped classes."""
    image_class_info, class_image_counts = compute_global_class_image_counts(
        pairs)

    kept_classes, dropped_classes = split_classes_by_min_image_count(
        class_image_counts=class_image_counts,
        min_source_images_per_class=min_source_images_per_class,
    )

    threshold = max(1, int(min_source_images_per_class))

    if not kept_classes:
        raise RuntimeError(
            "No classes left after filtering. "
            f"Check min_source_images_per_class={threshold}."
        )

    print()
    print(f"Global class filter: threshold={threshold}")
    print(f"Kept classes: {len(kept_classes)}")
    print(f"Dropped classes: {len(dropped_classes)}")
    print(f"Dropped list: {dropped_classes}")

    filtered_pairs = filter_pairs_by_kept_classes(
        image_class_info=image_class_info,
        kept_classes=set(kept_classes),
    )

    print(f"After class/image filtering: {len(filtered_pairs)}")

    return ClassFilterResult(
        pairs=filtered_pairs,
        classes=kept_classes,
    )
