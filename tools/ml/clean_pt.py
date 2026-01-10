from __future__ import annotations

from pathlib import Path
import argparse

from ultralytics.utils.torch_utils import strip_optimizer


# === Константы (constants) ===
# родительская папка (parent directory) для train-папок
TRAIN_ROOT_DIR = Path("D:/Downloads/proj/runs/detect")
# выбранная модель (selected weights file), например: "best.pt" или "last.pt"
WEIGHTS_FILE = "best.pt"
WEIGHTS_SUBDIR = "weights"            # подпапка (subdirectory), где лежат веса


def train_folder(train: str) -> str:
    """
    train (train run): папка прогона обучения.
    Примеры:
      "1" -> "train"
      "2" -> "train2"
      "train" -> "train"
      "train5" -> "train5"
    """
    t = train.strip()

    # Если пользователь уже передал "train" / "train2" / ...
    if t.startswith("train"):
        return t

    # Если передали номер "1", "2", ...
    if t.isdigit():
        n = int(t)
        if n <= 0:
            raise ValueError(
                "train должен быть положительным числом (positive integer).")
        return "train" if n == 1 else f"train{n}"

    raise ValueError(
        ('train должен быть числом ("1", "2", ...) или строкой вида '
         '"train", "train2", ...'))


def unique_path(path: Path) -> Path:
    """
    unique path (уникальный путь): подбирает имя файла так, чтобы не
    перезаписать существующий. Если path существует, создаёт path с суффиксом
    _2, _3, ...
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


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Strip optimizer (удалить optimizer-состояние) из YOLO .pt, "
            "не перезаписывая исходный файл."
        )
    )
    parser.add_argument(
        "--train",
        default="1",
        help=(
            'Номер/имя train (train run): "1"->train, "2"->train2", '
            'или "train5". По умолчанию: "1".'
        ),
    )
    args = parser.parse_args()

    run_dir = train_folder(args.train)
    src = TRAIN_ROOT_DIR / run_dir / WEIGHTS_SUBDIR / WEIGHTS_FILE

    if not src.exists():
        raise FileNotFoundError(f"Не найден файл (file not found): {src}")

    # Выходной файл (output file) — новый, рядом с исходным
    dst_default = src.with_name(f"{src.stem}_stripped{src.suffix}")
    dst = unique_path(dst_default)

    # Важно: передаём 's' (save path) => исходник не перезапишется
    strip_optimizer(f=src, s=str(dst))

    print(f"OK: исходный файл (source) не тронут: {src}")
    print(f"OK: сохранено (saved) в: {dst}")


if __name__ == "__main__":
    main()
