"""Dataset file writing utilities."""

from __future__ import annotations

from pathlib import Path

from ..system.io_utils import copy_or_link, ensure_dataset_dirs
from ..domain.models import ImageAnnotationPair
from ..voc.parser import yolo_lines_from_pair
from .yaml_writer import write_data_yaml


def make_unique_stem(pair: ImageAnnotationPair) -> str:
    """Create a stable output file stem and avoid region-name duplication."""
    base_name = pair.image_path.stem
    region_prefix = f"{pair.region}_"

    if base_name.lower().startswith(region_prefix.lower()):
        return base_name

    return f"{pair.region}_{base_name}"


def process_split(
    split_name: str,
    split_pairs: list[ImageAnnotationPair],
    class_to_id: dict[str, int],
    output_dir: Path,
    use_hardlinks: bool,
) -> None:
    """Copy/link images and write YOLO labels for one dataset split."""
    for pair in split_pairs:
        unique_stem = make_unique_stem(pair)

        output_image = (
            output_dir
            / "images"
            / split_name
            / f"{unique_stem}{pair.image_path.suffix.lower()}"
        )
        output_label = output_dir / "labels" / \
            split_name / f"{unique_stem}.txt"

        copy_or_link(
            pair.image_path,
            output_image,
            use_hardlink=use_hardlinks,
        )

        lines = yolo_lines_from_pair(pair, class_to_id)

        # Empty label files are valid YOLO negative samples.
        output_label.write_text("\n".join(lines), encoding="utf-8")


def write_dataset_files(
    output_dir: Path,
    train_pairs: list[ImageAnnotationPair],
    val_pairs: list[ImageAnnotationPair],
    test_pairs: list[ImageAnnotationPair],
    class_to_id: dict[str, int],
    classes: list[str],
    use_hardlinks: bool,
) -> None:
    """Create output directories, write images, labels, and data.yaml."""
    include_test = bool(test_pairs)

    ensure_dataset_dirs(output_dir, include_test=include_test)

    process_split(
        split_name="train",
        split_pairs=train_pairs,
        class_to_id=class_to_id,
        output_dir=output_dir,
        use_hardlinks=use_hardlinks,
    )

    process_split(
        split_name="val",
        split_pairs=val_pairs,
        class_to_id=class_to_id,
        output_dir=output_dir,
        use_hardlinks=use_hardlinks,
    )

    if include_test:
        process_split(
            split_name="test",
            split_pairs=test_pairs,
            class_to_id=class_to_id,
            output_dir=output_dir,
            use_hardlinks=use_hardlinks,
        )

    write_data_yaml(
        output_dir=output_dir,
        names=classes,
        include_test=include_test,
    )
