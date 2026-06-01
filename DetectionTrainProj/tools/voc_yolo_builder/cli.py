"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .workflow.builder import build_dataset
from .domain.models import BuildConfig


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert Pascal VOC XML annotations to a YOLO dataset."
    )

    parser.add_argument(
        "--source-root",
        type=str,
        required=True,
        help=(
            "Root directory of the source dataset. Expected layout: "
            "<region>/train/images and <region>/train/annotations/xmls."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory where the YOLO dataset will be written.",
    )
    parser.add_argument(
        "--max-output-images",
        type=int,
        default=20_000,
        help=(
            "Maximum number of images to include "
            "in the generated YOLO dataset."
        ),
    )
    parser.add_argument(
        "--sample-fraction",
        type=float,
        default=0.25,
        help=(
            "Fraction of eligible image/XML pairs to sample "
            "before train/val split."
        ),
    )
    parser.add_argument(
        "--validation-ratio",
        type=float,
        default=0.10,
        help=(
            "Fraction of the selected images to put into the validation split."
        ),
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.0,
        help=(
            "Fraction of selected images to put into the test split. "
            "Use 0.0 to skip test split creation."
        ),
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Seed used for shuffling and sampling.",
    )
    parser.add_argument(
        "--sampling-strategy",
        type=str,
        default="balanced",
        choices=["random", "balanced"],
        help=(
            "How to select images after filtering. "
            "'random' shuffles and takes the first N images. "
            "'balanced' tries to improve rare-class coverage first."
        ),
    )
    parser.add_argument(
        "--target-min-images-per-class",
        type=int,
        default=1_200,
        help=(
            "Target minimum number of selected images per class when using "
            "balanced sampling. This is best-effort, not guaranteed."
        ),
    )
    parser.add_argument(
        "--min-source-images-per-class",
        type=int,
        default=800,
        help=(
            "Drop classes that appear in fewer than this many images "
            "in the source dataset before sampling."
        ),
    )
    parser.add_argument(
        "--use-hardlinks",
        action="store_true",
        help=(
            "Create hard links for images instead of "
            "copying them when possible."
        ),
    )

    return parser.parse_args()


def config_from_args(args: argparse.Namespace) -> BuildConfig:
    """Create a BuildConfig object from parsed CLI arguments."""
    return BuildConfig(
        source_root=Path(args.source_root),
        output_dir=Path(args.output_dir),
        max_output_images=int(args.max_output_images),
        sample_fraction=float(args.sample_fraction),
        validation_ratio=float(args.validation_ratio),
        test_ratio=float(args.test_ratio),
        random_seed=int(args.random_seed),
        use_hardlinks=bool(args.use_hardlinks),
        sampling_strategy=str(args.sampling_strategy),
        target_min_images_per_class=int(args.target_min_images_per_class),
        min_source_images_per_class=int(args.min_source_images_per_class),
    )


def main() -> None:
    """CLI entry point."""
    args = parse_args()
    config = config_from_args(args)
    build_dataset(config)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
