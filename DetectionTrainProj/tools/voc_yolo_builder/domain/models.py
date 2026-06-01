"""Shared data models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VocObject:
    """Single annotated object from a Pascal VOC XML file."""

    class_name: str
    xmin: float
    ymin: float
    xmax: float
    ymax: float


@dataclass(frozen=True)
class ImageAnnotationPair:
    """Image path together with the matching Pascal VOC XML annotation."""

    image_path: Path
    xml_path: Path
    region: str


@dataclass(frozen=True)
class BuildConfig:
    """Configuration for building a YOLO dataset from Pascal VOC annotations."""

    source_root: Path
    output_dir: Path

    max_output_images: int = 20_000
    sample_fraction: float = 0.25
    validation_ratio: float = 0.10
    test_ratio: float = 0.0
    random_seed: int = 42

    use_hardlinks: bool = False
    sampling_strategy: str = "balanced"

    target_min_images_per_class: int = 1_200
    min_source_images_per_class: int = 800

    def validate(self) -> None:
        """Validate user-provided configuration values."""
        if not self.source_root.exists():
            raise FileNotFoundError(
                f"Source dataset root not found: {self.source_root}"
            )

        if not self.source_root.is_dir():
            raise NotADirectoryError(
                f"Source dataset root is not a directory: {self.source_root}"
            )

        if not 0.0 < self.sample_fraction <= 1.0:
            raise ValueError("sample_fraction must be in the range (0, 1].")

        if not 0.0 < self.validation_ratio < 1.0:
            raise ValueError("validation_ratio must be in the range (0, 1).")

        if not 0.0 <= self.test_ratio < 1.0:
            raise ValueError("test_ratio must be in the range [0, 1).")

        if self.validation_ratio + self.test_ratio >= 1.0:
            raise ValueError(
                "validation_ratio + test_ratio must be less than 1.0."
            )

        if self.max_output_images <= 0:
            raise ValueError("max_output_images must be positive.")

        if self.sampling_strategy not in {"random", "balanced"}:
            raise ValueError(
                "sampling_strategy must be either 'random' or 'balanced'."
            )

        if self.target_min_images_per_class < 0:
            raise ValueError(
                "target_min_images_per_class must be non-negative."
            )

        if self.min_source_images_per_class < 1:
            raise ValueError(
                "min_source_images_per_class must be at least 1."
            )
