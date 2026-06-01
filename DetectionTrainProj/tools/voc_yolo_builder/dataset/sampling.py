"""Dataset sampling strategies."""

from __future__ import annotations

import random
from collections import Counter
from typing import Dict, Iterable, List, Set, Tuple

from ..domain.models import ImageAnnotationPair
from ..voc.parser import parse_voc_xml


def compute_pair_classes(
    pairs: Iterable[ImageAnnotationPair],
    class_to_id: Dict[str, int],
) -> List[Tuple[ImageAnnotationPair, Set[str]]]:
    """Return each pair together with the set of known classes it contains."""
    pair_classes: List[Tuple[ImageAnnotationPair, Set[str]]] = []

    for pair in pairs:
        _, _, objects = parse_voc_xml(pair.xml_path)
        classes = {
            obj.class_name for obj in objects if obj.class_name in class_to_id}
        pair_classes.append((pair, classes))

    return pair_classes


def select_pairs_balanced(
    pairs: List[ImageAnnotationPair],
    class_to_id: Dict[str, int],
    limit: int,
    seed: int,
    min_images_per_class: int,
) -> List[ImageAnnotationPair]:
    """Select pairs while trying to cover rare classes first."""
    rng = random.Random(seed)
    pair_classes = compute_pair_classes(pairs, class_to_id)
    classes_by_pair = {pair: classes for pair, classes in pair_classes}

    class_image_counts = Counter()
    for _, classes in pair_classes:
        for class_name in classes:
            class_image_counts[class_name] += 1

    classes_by_rarity = sorted(
        class_image_counts.keys(),
        key=lambda class_name: class_image_counts[class_name],
    )

    selected: List[ImageAnnotationPair] = []
    selected_set = set()
    selected_image_counts = Counter()

    for class_name in classes_by_rarity:
        needed = max(
            0,
            int(min_images_per_class) -
            int(selected_image_counts.get(class_name, 0)),
        )
        if needed <= 0:
            continue

        candidates = [
            pair
            for pair, classes in pair_classes
            if class_name in classes and pair not in selected_set
        ]
        rng.shuffle(candidates)

        for pair in candidates:
            if len(selected) >= limit:
                break
            if pair in selected_set:
                continue

            selected.append(pair)
            selected_set.add(pair)

            for present_class in classes_by_pair[pair]:
                selected_image_counts[present_class] += 1

            needed -= 1
            if needed <= 0:
                break

        if len(selected) >= limit:
            break

    if len(selected) < limit:
        remaining = [pair for pair in pairs if pair not in selected_set]
        rng.shuffle(remaining)
        selected.extend(remaining[: max(0, limit - len(selected))])

    return selected[:limit]


def compute_sample_limit(
    total_count: int,
    sample_fraction: float,
    max_output_images: int,
) -> int:
    """Compute the final sample size from fraction and max image constraints."""
    if total_count <= 0:
        return 0

    fraction_limit = max(1, int(total_count * sample_fraction))
    return min(total_count, int(max_output_images), fraction_limit)


def select_output_pairs(
    pairs: list[ImageAnnotationPair],
    class_to_id: dict[str, int],
    rng: random.Random,
    sample_fraction: float,
    max_output_images: int,
    sampling_strategy: str,
    random_seed: int,
    target_min_images_per_class: int,
) -> list[ImageAnnotationPair]:
    """Select the final image subset according to the configured sampling strategy."""
    rng.shuffle(pairs)

    total_count = len(pairs)
    limit = compute_sample_limit(
        total_count=total_count,
        sample_fraction=sample_fraction,
        max_output_images=max_output_images,
    )

    print(
        f"Sampling fraction={sample_fraction}, "
        f"max_output_images={max_output_images}, "
        f"limit={limit} of {total_count}"
    )

    if sampling_strategy == "balanced":
        selected_pairs = select_pairs_balanced(
            pairs=pairs,
            class_to_id=class_to_id,
            limit=limit,
            seed=random_seed,
            min_images_per_class=target_min_images_per_class,
        )
    else:
        selected_pairs = pairs[:limit]

    rng.shuffle(selected_pairs)
    return selected_pairs
