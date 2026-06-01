"""Source dataset discovery."""

from __future__ import annotations

from pathlib import Path
from typing import List

from ..domain.constants import IMG_EXTENSIONS
from ..domain.models import ImageAnnotationPair


def find_train_pairs(root: Path) -> List[ImageAnnotationPair]:
    """Find image/XML pairs in <region>/train/images and annotations/xmls."""
    pairs: List[ImageAnnotationPair] = []

    for images_dir in root.glob("*/*/images"):
        if len(images_dir.parts) < 2 or images_dir.parts[-2].lower() != "train":
            continue

        region_dir = images_dir.parent.parent
        xml_dir = region_dir / "train" / "annotations" / "xmls"
        if not xml_dir.exists():
            continue

        for image_path in images_dir.iterdir():
            if image_path.suffix.lower() not in IMG_EXTENSIONS:
                continue

            xml_path = xml_dir / f"{image_path.stem}.xml"
            if xml_path.exists():
                pairs.append(
                    ImageAnnotationPair(
                        image_path=image_path,
                        xml_path=xml_path,
                        region=region_dir.name,
                    )
                )

    return pairs


def discover_source_pairs(source_root: Path) -> list[ImageAnnotationPair]:
    """Find source image/XML pairs and fail early when none are found."""
    pairs = find_train_pairs(source_root)

    if not pairs:
        raise RuntimeError(
            "No image/XML pairs found. Check the source folder "
            "structure and paths."
        )

    print(f"Found image/XML pairs: {len(pairs)}")
    return pairs
