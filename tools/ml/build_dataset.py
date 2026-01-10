"""
Pascal VOC XML -> YOLO labels dataset builder (Windows-friendly).

Термины:
- Pascal VOC XML: формат аннотаций (annotations - разметка) в XML,
  где объекты описаны <object><bndbox>...
- YOLO labels: текстовый файл .txt, где каждая строка:
  class_id x_center y_center width height (все normalized = нормализованы 0..1)
- train/val split: разбиение данных на обучение (train) и проверку (val)
- subset: подмножество (часть) изображений для ускорения подготовки
  и обучения
- hardlink: жёсткая ссылка (быстро, без копирования данных на диск),
  работает на NTFS
"""

from __future__ import annotations

import argparse
import os
import random
import shutil
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
from collections import Counter
from pretty_output import print_table

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


# -----------------------------
# Helpers (вспомогательные функции)
# -----------------------------

def to_float(text: Optional[str]) -> Optional[float]:
    """
    float (вещественное число) - число с дробной частью.
    Поддерживаем десятичную точку '.' и запятую ','.
    """
    if text is None:
        return None
    t = text.strip()
    if not t:
        return None
    t = t.replace(",", ".")
    return float(t)


def clip(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """
    clip (клиппинг) - ограничить значение диапазоном [lo, hi].
    """
    return min(max(v, lo), hi)


def try_hardlink(src: Path, dst: Path) -> bool:
    """
    hardlink (жёсткая ссылка) - второй путь к тому же файлу
    без копирования данных. Возвращает True, если получилось, иначе False.
    """
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            return True
        os.link(src, dst)
        return True
    except Exception:
        return False


def copy_or_link(src: Path, dst: Path, use_hardlink: bool) -> None:
    """
    Если use_hardlink=True, пытаемся hardlink, иначе делаем copy2
    (копирование с метаданными).
    """
    if use_hardlink and try_hardlink(src, dst):
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def read_image_size_with_pillow(image_path: Path) -> Tuple[int, int]:
    """
    Pillow (PIL) - библиотека для работы с изображениями.
    Нужна как запасной вариант, если в XML некорректный <size>.
    """
    try:
        from PIL import Image  # Pillow package (пакет Pillow)
    except Exception as e:
        raise RuntimeError(
            "Нужно установить Pillow, чтобы читать размер картинки,\n"
            "когда <size> в XML плохой.\n"
            "Установка: pip install pillow"
        ) from e

    with Image.open(image_path) as im:
        w, h = im.size
    return int(w), int(h)


def count_class_stats_from_labels(
    label_paths: Iterable[Path],
) -> Tuple[Counter, Counter, int, int]:
    """
    Статистика по уже записанным label-файлам.

    Термины:
    - label file (файл меток) - txt с YOLO строками: cls_id x y w h
    - images_per_class - сколько изображений содержит класс хотя бы один раз
    - instances_per_class - сколько объектов (строк) класса всего
    - total_images - всего изображений в сплите
    - total_instances - всего объектов во всём сплите
    """
    instances_per_class: Counter = Counter()
    images_per_class: Counter = Counter()

    total_images = 0
    total_instances = 0

    for lp in label_paths:
        total_images += 1
        if not lp.exists():
            continue

        text = lp.read_text(encoding="utf-8").strip()
        if not text:
            continue

        # set (множество) - уникальные значения без повторов
        seen_in_image = set()

        for line in text.splitlines():
            parts = line.strip().split()
            if not parts:
                continue
            cls_id = int(parts[0])

            instances_per_class[cls_id] += 1
            total_instances += 1
            seen_in_image.add(cls_id)

        for cls_id in seen_in_image:
            images_per_class[cls_id] += 1

    return images_per_class, instances_per_class, total_images, total_instances


def print_class_stats(
    title: str,
    classes: List[str],
    images_per_class: Counter,
    instances_per_class: Counter,
    total_images: int,
    total_instances: int,
) -> None:
    """
    Печать статистики по классам через pretty_output.print_table.

    normalized (нормализованный) - доля от общего числа.
    """
    print()
    print(title)
    print(f"Number of classes (число классов): {len(classes)}")
    print(f"Total images (всего изображений): {total_images}")
    print(f"Total instances (всего объектов/рамок): {total_instances}")
    print()

    # header (заголовок) - имена колонок
    header = ["id", "class", "images", "images_norm", "instances", "inst_norm"]

    # rows (строки) - значения по колонкам
    rows = []
    for cls_id, cls_name in enumerate(classes):
        img_cnt = int(images_per_class.get(cls_id, 0))
        inst_cnt = int(instances_per_class.get(cls_id, 0))

        img_norm = (img_cnt / total_images) if total_images > 0 else 0.0
        inst_norm = (
            inst_cnt / total_instances) if total_instances > 0 else 0.0

        # Чтобы было ровно 4 знака после точки, делаем строку.
        # string (строка) - текстовый тип данных.
        rows.append([
            cls_id,
            cls_name,
            img_cnt,
            f"{img_norm:.4f}",
            inst_cnt,
            f"{inst_norm:.4f}",
        ])

    # print_table (печать таблицы) - форматирует и печатает
    print_table(header, rows)


# -----------------------------
# VOC parsing (разбор VOC XML)
# -----------------------------

@dataclass
class VocObject:
    """
    Object (объект) - один размеченный экземпляр на изображении.
    """
    cls_name: str
    xmin: float
    ymin: float
    xmax: float
    ymax: float


def parse_voc_xml(
    xml_path: Path,
) -> Tuple[Optional[float], Optional[float], List[VocObject]]:
    """
    Парсим (parse - читаем и извлекаем данные) VOC XML.

    Возвращаем:
    - w, h: width/height (ширина/высота) из <size>, могут быть float
    - objects: список объектов (list of objects), может быть пустым (empty)
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size = root.find("size")
    w = to_float(size.findtext("width") if size is not None else None)
    h = to_float(size.findtext("height") if size is not None else None)

    objects: List[VocObject] = []
    for obj in root.findall("object"):
        name = (obj.findtext("name") or "").strip()
        b = obj.find("bndbox")
        if not name or b is None:
            continue

        xmin = to_float(b.findtext("xmin"))
        ymin = to_float(b.findtext("ymin"))
        xmax = to_float(b.findtext("xmax"))
        ymax = to_float(b.findtext("ymax"))

        # invalid (некорректно) - если чего-то не хватает
        if None in (xmin, ymin, xmax, ymax):
            continue

        # swap (поменять местами), если углы перепутаны
        if xmax < xmin:
            xmin, xmax = xmax, xmin
        if ymax < ymin:
            ymin, ymax = ymax, ymin

        objects.append(VocObject(name, xmin, ymin, xmax, ymax))

    return w, h, objects


def voc_bbox_to_yolo(
    xmin: float,
    ymin: float,
    xmax: float,
    ymax: float,
    w: float,
    h: float,
) -> Tuple[float, float, float, float]:
    """
    VOC bbox (xmin,ymin,xmax,ymax) -> YOLO bbox
    (x_center,y_center,width,height)

    normalized (нормализовано) - делим на ширину/высоту,
    чтобы получить диапазон 0..1.
    """
    bw = max(0.0, (xmax - xmin) / w)
    bh = max(0.0, (ymax - ymin) / h)
    xc = ((xmin + xmax) / 2.0) / w
    yc = ((ymin + ymax) / 2.0) / h
    return xc, yc, bw, bh


# -----------------------------
# Dataset discovery (поиск данных)
# -----------------------------

@dataclass(frozen=True)
class Pair:
    """
    Pair (пара) - изображение + XML разметка для этого изображения.
    """
    image_path: Path
    xml_path: Path
    # region (регион/поднабор) - имя верхней папки, например Norway
    region: str


def find_train_pairs(root: Path) -> List[Pair]:
    """
    Ищем директории вида:
      <region>/train/images
      <region>/train/annotations/xmls
    """
    pairs: List[Pair] = []
    for images_dir in root.glob("*/*/images"):
        # ожидаем, что это .../<region>/train/images
        if images_dir.parts[-2].lower() != "train":
            continue

        region_dir = images_dir.parent.parent  # .../<region>
        xml_dir = region_dir / "train" / "annotations" / "xmls"
        if not xml_dir.exists():
            continue

        region_name = region_dir.name

        for img_path in images_dir.iterdir():
            if img_path.suffix.lower() not in IMG_EXTS:
                continue
            xml_path = xml_dir / f"{img_path.stem}.xml"
            if xml_path.exists():
                pairs.append(Pair(img_path, xml_path, region_name))

    return pairs


def select_pairs_balanced(
    pairs: List[Pair],
    class_to_id: dict,
    limit: int,
    seed: int,
    min_images_per_class: int,
) -> List[Pair]:
    """
    Выбираем limit изображений так, чтобы каждый класс встретился
    минимум min_images_per_class раз (если это возможно).

    Термины:
    - coverage (покрытие) - наличие класса в выбранном наборе
    - candidate (кандидат) - элемент, который можно выбрать
    """
    random.seed(seed)

    # Для каждого pair заранее узнаём какие классы в нём есть
    pair_classes: List[Tuple[Pair, set]] = []
    for p in pairs:
        _, _, objs = parse_voc_xml(p.xml_path)
        s = set(o.cls_name for o in objs if o.cls_name in class_to_id)
        pair_classes.append((p, s))

    # Сколько изображений содержит каждый класс во ВСЁМ датасете
    class_freq_images = Counter()
    for _, s in pair_classes:
        for c in s:
            class_freq_images[c] += 1

    # Классы сортируем от самых редких к самым частым
    classes_by_rarity = sorted(
        class_freq_images.keys(), key=lambda c: class_freq_images[c])

    selected: List[Pair] = []
    # set - множество для быстрого membership (проверка "уже выбран?")
    selected_set = set()

    # Счётчик: сколько раз класс уже попал в выбранные изображения
    selected_images_per_class = Counter()

    # 1) Сначала добиваем минимальное покрытие редких классов
    for cls_name in classes_by_rarity:
        need = max(0, int(min_images_per_class) -
                   int(selected_images_per_class.get(cls_name, 0)))
        if need <= 0:
            continue

        # Все кандидаты, где есть cls_name и которых ещё нет в selected
        candidates = [p for p, s in pair_classes if (
            cls_name in s and p not in selected_set)]
        random.shuffle(candidates)

        for p in candidates:
            if len(selected) >= limit:
                break
            if p in selected_set:
                continue
            selected.append(p)
            selected_set.add(p)

            # обновляем счётчики
            _, s = next((pp, ss) for pp, ss in pair_classes if pp == p)
            for c in s:
                selected_images_per_class[c] += 1

            need -= 1
            if need <= 0:
                break

        if len(selected) >= limit:
            break

    # 2) Дальше добираем до limit случайно (для разнообразия данных)
    if len(selected) < limit:
        remaining = [p for p in pairs if p not in selected_set]
        random.shuffle(remaining)
        selected.extend(remaining[: max(0, limit - len(selected))])

    return selected[:limit]


# -----------------------------
# YAML writer (конфиг датасета)
# -----------------------------

def write_data_yaml(out_dir: Path, names: List[str]) -> None:
    """
    data.yaml - конфигурация (config) датасета для Ultralytics.

    names: список названий классов (class names).
    """
    yaml_path = out_dir / "data.yaml"
    lines: List[str] = []
    lines.append(f"path: {out_dir.as_posix()}")
    lines.append("train: images/train")
    lines.append("val: images/val")
    lines.append("names:")
    for i, n in enumerate(names):
        lines.append(f"  {i}: {n}")
    yaml_path.write_text("\n".join(lines), encoding="utf-8")


# -----------------------------
# Main build logic (основная логика)
# -----------------------------

def make_unique_stem(pair: Pair) -> str:
    """
    Делаем уникальное имя (unique name), чтобы избежать коллизий
    (collision - конфликт имён). Обычно имена уже уникальные, но это
    страховка.
    """
    base = pair.image_path.stem
    # если уже начинается с региона, не удваиваем
    if base.lower().startswith(pair.region.lower() + "_"):
        return base
    return f"{pair.region}_{base}"


def build_dataset(
    root: Path,
    out_dir: Path,
    max_images: int,
    fraction: float,
    val_ratio: float,
    seed: int,
    use_hardlink: bool,
    sampling: str,
    min_images_per_class: int,
    min_global_images_per_class: int,
) -> None:
    random.seed(seed)

    # --------- helpers (вспомогательные функции) ---------

    def compute_global_class_image_counts(
        pairs: list[Pair],
    ) -> tuple[list[tuple[Pair, bool, set[str]]], Counter]:
        """
        Counter (счётчик) - словарь вида {ключ: сколько раз встретился}.
        set (множество) - уникальные значения без повторов.
        """
        class_images = Counter()
        # per_image_info (инфо по изображению) - (пара, есть_ли_объекты,
        # множество_классов)
        per_image_info: list[tuple[Pair, bool, set[str]]] = []

        for p in pairs:
            _, _, objs = parse_voc_xml(p.xml_path)

            # has_objects (есть ли объекты) - True, если в XML есть хотя бы
            # один <object>
            has_objects = len(objs) > 0

            # present (присутствующие классы) - уникальные имена классов
            # на изображении
            present = set(o.cls_name for o in objs if o.cls_name)

            per_image_info.append((p, has_objects, present))

            # global_images_per_class (глобальные "изображения на класс")
            # считаем по изображениям, то есть класс +1, если встретился на
            # картинке хотя бы раз
            for c in present:
                class_images[c] += 1

        return per_image_info, class_images

    def apply_global_class_filter(
        class_images: Counter,
        threshold: int,
    ) -> tuple[list[str], list[str]]:
        """
        threshold (порог) - минимальное значение, чтобы «пройти фильтр».
        """
        kept = sorted([c for c, n in class_images.items() if n >= threshold])
        dropped = sorted([c for c, n in class_images.items() if n < threshold])
        return kept, dropped

    def filter_pairs_by_kept_classes(
        per_image_info: list[tuple[Pair, bool, set[str]]],
        kept_set: set[str],
    ) -> list[Pair]:
        """
        Оставляем:
        - empty objects (нет объектов) -> негатив (negative sample)
        - есть объекты и есть хотя бы один kept class

        Выкидываем:
        - есть объекты, но все классы только из dropped (мусорных)
        (то есть пересечение с kept_set пустое)
        """
        kept_with_objects = 0
        kept_empty_objects = 0
        dropped_only = 0

        filtered: list[Pair] = []

        for p, has_objects, present in per_image_info:
            if not has_objects:
                kept_empty_objects += 1
                filtered.append(p)
                continue

            if present & kept_set:
                kept_with_objects += 1
                filtered.append(p)
            else:
                dropped_only += 1

        print("Filter results (результаты фильтра):")
        print("  kept_with_objects (оставили с объектами):", kept_with_objects)
        print(
            "  kept_empty_objects (оставили без объектов):",
            kept_empty_objects
        )
        print(
            "  dropped_only_dropped_classes (выкинули только мусорные):",
            dropped_only
        )

        return filtered

    def compute_limit(raw_len: int, fraction: float, max_images: int) -> int:
        """
        limit (лимит) - сколько пар изображений реально берём в подвыборку.
        """
        if raw_len <= 0:
            return 0
        limit = max(1, int(raw_len * fraction))
        return min(raw_len, int(max_images), int(limit))

    def ensure_output_dirs(out_dir: Path) -> None:
        """
        directory (директория) - папка на диске.
        """
        for p in (
            out_dir / "images" / "train",
            out_dir / "images" / "val",
            out_dir / "labels" / "train",
            out_dir / "labels" / "val",
        ):
            p.mkdir(parents=True, exist_ok=True)

    def yolo_lines_from_pair(
        pair: Pair, class_to_id: dict[str, int]
    ) -> list[str]:
        """
        YOLO line (строка YOLO) - "class_id x_center y_center width height".
        fallback (запасной вариант) - используем Pillow, если XML <size>
        плохой.
        """
        w, h, objs = parse_voc_xml(pair.xml_path)

        if not w or not h or w <= 1 or h <= 1:
            iw, ih = read_image_size_with_pillow(pair.image_path)
            w, h = float(iw), float(ih)

        lines: list[str] = []
        for o in objs:
            cls_id = class_to_id.get(o.cls_name)
            if cls_id is None:
                continue

            xc, yc, bw, bh = voc_bbox_to_yolo(
                o.xmin, o.ymin, o.xmax, o.ymax, w, h)

            # clip (клиппинг) - ограничить диапазоном [0..1]
            xc, yc, bw, bh = clip(xc), clip(yc), clip(bw), clip(bh)

            # degenerate box (вырожденный бокс) - нулевая ширина/высота
            if bw <= 0.0 or bh <= 0.0:
                continue

            lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}")

        return lines

    def process_split(
        split_name: str,
        split_pairs: Iterable[Pair],
        class_to_id: dict[str, int],
    ) -> None:
        """
        split (сплит) - часть датасета: train или val.
        """
        for pair in split_pairs:
            uniq_stem = make_unique_stem(pair)

            dst_img = (
                out_dir / "images" / split_name /
                f"{uniq_stem}{pair.image_path.suffix.lower()}"
            )
            dst_lbl = out_dir / "labels" / split_name / f"{uniq_stem}.txt"

            copy_or_link(pair.image_path, dst_img, use_hardlink=use_hardlink)

            lines = yolo_lines_from_pair(pair, class_to_id)

            # пустой файл тоже пишем: это “negative sample”
            # (негативный пример) без объектов
            dst_lbl.write_text("\n".join(lines), encoding="utf-8")

    # --------- main flow (основной поток) ---------

    pairs = find_train_pairs(root)
    if not pairs:
        raise RuntimeError(
            "Не нашёл ни одной пары image+xml. "
            "Проверь структуру папок и пути."
        )
    print(f"Found pairs (нашёл пар image+xml): {len(pairs)}")

    per_image_info, class_images = compute_global_class_image_counts(pairs)

    thr = max(1, int(min_global_images_per_class))
    kept_classes, dropped_classes = apply_global_class_filter(
        class_images, thr)

    if not kept_classes:
        raise RuntimeError(
            f"After filtering, no classes left. "
            f"Check --min-global-images-per-class={thr}."
        )

    print()
    print(f"Global class filter (глобальный фильтр классов): threshold={thr}")
    print(f"Kept classes (оставили): {len(kept_classes)}")
    print(f"Dropped classes (выкинули): {len(dropped_classes)}")
    print(f"Dropped list: {dropped_classes}")

    kept_set = set(kept_classes)
    pairs = filter_pairs_by_kept_classes(per_image_info, kept_set)

    print(
        "After class+image filter (после фильтра классов/картинок):",
        len(pairs)
    )

    classes = kept_classes
    class_to_id = {c: i for i, c in enumerate(classes)}

    random.shuffle(pairs)

    raw_len = len(pairs)
    limit = compute_limit(raw_len, fraction, max_images)
    print(
        f"Sampling fraction={fraction}, max_images={max_images}, "
        f"limit={limit} of {raw_len}"
    )

    if sampling == "balanced":
        pairs = select_pairs_balanced(
            pairs=pairs,
            class_to_id=class_to_id,
            limit=limit,
            seed=seed,
            min_images_per_class=min_images_per_class,
        )
    else:
        pairs = pairs[:limit]

    # Чтобы не было перекоса: перемешиваем перед split
    random.shuffle(pairs)

    # n_val (число val) - размер валидации
    if len(pairs) == 1:
        n_val = 1
    else:
        n_val = max(1, int(len(pairs) * val_ratio))
        n_val = min(n_val, len(pairs) - 1)  # гарантируем хотя бы 1 train

    val_pairs = pairs[:n_val]
    train_pairs = pairs[n_val:]

    ensure_output_dirs(out_dir)

    process_split("train", train_pairs, class_to_id)
    process_split("val", val_pairs, class_to_id)

    write_data_yaml(out_dir, classes)

    print("OK: dataset built")
    print(f"Root (корень): {root}")
    print(f"Out (выход): {out_dir}")
    print(f"Classes (классы): {len(classes)} -> {classes}")
    print(f"Train images (обучение): {len(train_pairs)}")
    print(f"Val images (валидация): {len(val_pairs)}")
    print(f"data.yaml: {out_dir / 'data.yaml'}")

    train_label_paths = list((out_dir / "labels" / "train").glob("*.txt"))
    val_label_paths = list((out_dir / "labels" / "val").glob("*.txt"))

    tr_img, tr_inst, tr_total_images, tr_total_inst = \
        count_class_stats_from_labels(train_label_paths)
    va_img, va_inst, va_total_images, va_total_inst = \
        count_class_stats_from_labels(val_label_paths)

    print_class_stats(
        title="TRAIN split stats (статистика train):",
        classes=classes,
        images_per_class=tr_img,
        instances_per_class=tr_inst,
        total_images=tr_total_images,
        total_instances=tr_total_inst,
    )

    print_class_stats(
        title="VAL split stats (статистика val):",
        classes=classes,
        images_per_class=va_img,
        instances_per_class=va_inst,
        total_images=va_total_images,
        total_instances=va_total_inst,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert Pascal VOC XML to YOLO labels and build "
            "Ultralytics dataset."
        )
    )

    parser.add_argument("--root", type=str, required=True,
                        help="Root folder with your DATA (корневая папка).")
    parser.add_argument("--out", type=str, required=True,
                        help="Output folder for YOLO dataset "
                             "(выходная папка).")

    parser.add_argument("--max-images", type=int, default=20_000,
                        help="Cap images for speed (максимум изображений).")
    parser.add_argument("--fraction", type=float, default=0.25,
                        help="Fraction of all pairs to use (доля данных).")
    parser.add_argument("--val-ratio", type=float, default=0.10,
                        help="Validation split ratio (доля val).")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (зерно случайности).")

    parser.add_argument(
        "--sampling",
        type=str,
        default="balanced",
        choices=["random", "balanced"],
        help=(
            "Sampling strategy (стратегия выборки): "
            "random=случайно, balanced=с покрытием редких классов."
        ),
    )

    parser.add_argument(
        "--min-images-per-class",
        type=int,
        default=1200,
        help=(
            "Minimum images per class in the selected subset "
            "(минимум изображений на класс в подвыборке)."
        ),
    )

    parser.add_argument(
        "--min-global-images-per-class",
        type=int,
        default=800,
        help=(
            "Drop classes that appear in fewer than N images "
            "in the full dataset "
            "(выкинуть классы, которые встречаются менее чем в N "
            "изображениях во всём исходном датасете)."
        ),
    )

    parser.add_argument(
        "--hardlink",
        action="store_true",
        help="Enable hardlink instead of copy "
             "(включить hardlink вместо копирования).",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root)
    out_dir = Path(args.out)

    if not root.exists():
        raise FileNotFoundError(f"Root folder not found: {root}")

    out_dir.mkdir(parents=True, exist_ok=True)

    if not (0.0 < args.fraction <= 1.0):
        raise ValueError("--fraction must be in (0, 1].")
    if not (0.0 < args.val_ratio < 1.0):
        raise ValueError("--val-ratio must be in (0, 1).")

    build_dataset(
        root=root,
        out_dir=out_dir,
        max_images=int(args.max_images),
        fraction=float(args.fraction),
        val_ratio=float(args.val_ratio),
        seed=int(args.seed),
        use_hardlink=bool(args.hardlink),
        sampling=str(args.sampling),
        min_images_per_class=int(args.min_images_per_class),
        min_global_images_per_class=int(args.min_global_images_per_class),
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise
