#!/usr/bin/env python3
"""
Randomly sample images from */test/images/ folders under a given root
directory.

Default behavior:
- Flat output (flat = all selected images are copied directly into the
  output folder).
  If name collisions happen (collision = same filename appears twice),
  the script adds a suffix like _1, _2, etc.

What the script does:
- Recursively finds folders named "test" under the given input root
  (recursive = scans subfolders).
- For each ".../test" folder, checks for ".../test/images"
  (images folder = child folder named "images").
- Collects image files from all such images folders
  (image file = file with image extension like .jpg).
- Randomly selects N images (sample = randomly choose; without replacement = no
  duplicates).
- Copies (or optionally moves) selected images into the output folder.
"""

from __future__ import annotations

import argparse
import random
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set


DEFAULT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tif", ".tiff", ".webp"
}


@dataclass(frozen=True)
class CollectedImage:
    """Record (record = structured data) describing a found image."""
    path: Path
    source_images_dir: Path


def find_test_images_dirs(root: Path) -> List[Path]:
    """
    Find directories named 'test' and return existing 'images' subdirectories
    under them.

    Returns:
        List of Path objects pointing to ".../test/images" directories.
    """
    images_dirs: List[Path] = []
    # rglob: recursive glob (glob = pattern-based search)
    for test_dir in root.rglob("test"):
        if test_dir.is_dir():
            images_dir = test_dir / "images"
            if images_dir.is_dir():
                images_dirs.append(images_dir)
    return images_dirs


def collect_images(
    images_dirs: Iterable[Path],
    extensions: Set[str]
) -> List[CollectedImage]:
    """
    Collect image files from given directories.

    Args:
        images_dirs: directories to scan
        extensions: allowed file suffixes (suffix = extension like ".png")

    Returns:
        List of CollectedImage objects.
    """
    collected: List[CollectedImage] = []
    for images_dir in images_dirs:
        for p in images_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in extensions:
                collected.append(CollectedImage(
                    path=p, source_images_dir=images_dir))
    return collected


def copy_with_collision_safe_name(src: Path, dst_dir: Path) -> Path:
    """
    Copy src into dst_dir using collision-safe naming.

    Collision-safe naming: if "a.jpg" already exists, write "a_1.jpg",
    then "a_2.jpg", etc.

    Returns:
        Final destination path.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)

    base = src.stem  # stem: filename without extension
    ext = src.suffix
    dst = dst_dir / f"{base}{ext}"

    counter = 1
    while dst.exists():
        dst = dst_dir / f"{base}_{counter}{ext}"
        counter += 1

    shutil.copy2(src, dst)  # copy2: copy content + metadata (timestamps)
    return dst


def move_with_collision_safe_name(src: Path, dst_dir: Path) -> Path:
    """
    Move src into dst_dir using collision-safe naming.

    Move: the source file is removed from its original location after transfer.

    Returns:
        Final destination path.
    """
    dst_dir.mkdir(parents=True, exist_ok=True)

    base = src.stem
    ext = src.suffix
    dst = dst_dir / f"{base}{ext}"

    counter = 1
    while dst.exists():
        dst = dst_dir / f"{base}_{counter}{ext}"
        counter += 1

    shutil.move(str(src), str(dst))
    return dst


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recursively find */test/images images, randomly sample N, "
            "and copy to output (flat by default)."
        )
    )
    parser.add_argument(
        "input_root",
        type=Path,
        help=(
            "Input root folder "
            "(root folder = starting point for recursive search)."
        ),
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help=(
            "Output folder (output folder = destination directory "
            "for sampled images)."
        ),
    )
    parser.add_argument(
        "-n",
        "--num",
        type=int,
        required=True,
        help=("Number of images to sample "
              "(N = how many images to randomly pick)."),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=(
            "Random seed (seed = fixed number to make randomness "
            "reproducible)."
        ),
    )
    parser.add_argument(
        "--extensions",
        type=str,
        default=",".join(sorted(DEFAULT_EXTENSIONS)),
        help="Comma-separated allowed extensions, e.g. .jpg,.png,.webp",
    )
    parser.add_argument(
        "--move",
        action="store_true",
        help=(
            "Move instead of copy (move = remove originals after placing into "
            "output)."
        ),
    )

    args = parser.parse_args()

    input_root: Path = args.input_root.resolve()
    output_dir: Path = args.output_dir.resolve()
    n: int = args.num

    if n <= 0:
        print("ERROR: --num must be a positive integer.", file=sys.stderr)
        return 2

    if not input_root.is_dir():
        print(
            f"ERROR: input_root is not a directory: {input_root}",
            file=sys.stderr
        )
        return 2

    extensions = {e.strip().lower()
                  for e in args.extensions.split(",") if e.strip()}
    if not extensions:
        print("ERROR: extensions list is empty.", file=sys.stderr)
        return 2

    if args.seed is not None:
        random.seed(args.seed)

    images_dirs = find_test_images_dirs(input_root)
    if not images_dirs:
        print(f"No 'test/images' directories found under: {input_root}")
        return 0

    all_images = collect_images(images_dirs, extensions)
    if not all_images:
        print("No images found in any 'test/images' directories.")
        return 0

    available = len(all_images)
    if n > available:
        print(
            f"Requested N={n}, but only {available} images exist. "
            f"Will sample {available}."
        )
        n = available

    sampled = random.sample(all_images, k=n)

    copied_or_moved = 0
    for item in sampled:
        src = item.path
        if args.move:
            dst = move_with_collision_safe_name(src, output_dir)
        else:
            dst = copy_with_collision_safe_name(src, output_dir)

        copied_or_moved += 1
        print(f"[{copied_or_moved}/{n}] {src} -> {dst}")

    print(
        f"Done. {'Moved' if args.move else 'Copied'} {copied_or_moved} images "
        f"to: {output_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
