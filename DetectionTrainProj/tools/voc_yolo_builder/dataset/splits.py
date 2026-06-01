"""Dataset split utilities."""

from __future__ import annotations

from ..domain.models import ImageAnnotationPair


def split_train_val_test(
    pairs: list[ImageAnnotationPair],
    validation_ratio: float,
    test_ratio: float,
) -> tuple[
    list[ImageAnnotationPair],
    list[ImageAnnotationPair],
    list[ImageAnnotationPair],
]:
    """Split selected pairs into train, validation, and optional test subsets."""
    total = len(pairs)

    if total == 0:
        return [], [], []

    if total == 1:
        return [], pairs, []

    test_count = int(total * test_ratio)
    validation_count = int(total * validation_ratio)

    if validation_ratio > 0.0:
        validation_count = max(1, validation_count)

    if test_ratio > 0.0:
        test_count = max(1, test_count)

    if validation_count + test_count >= total:
        overflow = validation_count + test_count - total + 1

        if test_count >= overflow:
            test_count -= overflow
        else:
            overflow -= test_count
            test_count = 0
            validation_count = max(0, validation_count - overflow)

    validation_pairs = pairs[:validation_count]
    test_pairs = pairs[validation_count: validation_count + test_count]
    train_pairs = pairs[validation_count + test_count:]

    return train_pairs, validation_pairs, test_pairs
