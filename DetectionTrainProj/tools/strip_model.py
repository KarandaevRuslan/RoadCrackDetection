from __future__ import annotations

from pathlib import Path
import argparse

from ultralytics.utils.torch_utils import strip_optimizer


def unique_path(path: Path) -> Path:
    """
    Подбирает уникальный путь, чтобы не перезаписать существующий файл.
    Если файл уже есть, добавляет суффикс _2, _3, ...
    """
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent

    i = 2
    while True:
        candidate = parent / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def strip_yolo_model(model_path: str | Path) -> Path:
    """
    Удаляет optimizer/state из YOLO .pt модели и сохраняет облегченную копию
    рядом с исходным файлом.

    Пример:
        D:/runs/train/weights/best.pt
        -> D:/runs/train/weights/best_stripped.pt
    """
    src = Path(model_path).expanduser().resolve()

    if not src.exists():
        raise FileNotFoundError(f"Файл модели не найден: {src}")

    if src.suffix.lower() != ".pt":
        raise ValueError(f"Ожидался .pt файл, получено: {src}")

    dst_default = src.with_name(f"{src.stem}_stripped{src.suffix}")
    dst = unique_path(dst_default)

    # s=... нужен, чтобы не перезаписать исходный файл
    strip_optimizer(f=src, s=str(dst))

    return dst


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Создает облегченную копию YOLO .pt модели рядом с исходным файлом "
            "без перезаписи оригинала."
        )
    )

    parser.add_argument(
        "model",
        type=str,
        help="Полный путь до .pt модели, например: D:/runs/train/weights/best.pt",
    )

    args = parser.parse_args()

    src = Path(args.model).expanduser().resolve()
    dst = strip_yolo_model(src)

    print(f"OK: исходная модель не изменена:")
    print(src)
    print()
    print(f"OK: облегченная модель сохранена:")
    print(dst)


if __name__ == "__main__":
    main()
