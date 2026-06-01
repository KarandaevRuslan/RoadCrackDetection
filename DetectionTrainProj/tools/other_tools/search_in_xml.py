import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Рекурсивно ищет .xml файлы и выводит те, "
            "что содержат заданную строку."
        )
    )

    parser.add_argument(
        "root",
        type=Path,
        help="Путь (path) к папке, в которой искать рекурсивно."
    )

    parser.add_argument(
        "needle",
        help="Искомая строка (string), которую нужно найти в содержимом XML."
    )

    parser.add_argument(
        "--pattern",
        default="*.xml",
        help=(
            "Маска (glob pattern) имен файлов. "
            "По умолчанию (default) '*.xml'."
        )
    )

    parser.add_argument(
        "--encoding",
        default="utf-8",
        help=(
            "Кодировка (encoding) чтения файлов. "
            "По умолчанию (default) 'utf-8'."
        )
    )

    parser.add_argument(
        "--ignore-errors",
        action="store_true",
        help="Флаг (flag): игнорировать ошибки чтения/декодирования (errors)."
    )

    args = parser.parse_args()

    root: Path = args.root
    needle: str = args.needle
    pattern: str = args.pattern
    encoding: str = args.encoding
    errors_mode: str = "ignore" if args.ignore_errors else "strict"

    if not root.exists():
        raise SystemExit(f"Путь не существует (path does not exist): {root}")
    if not root.is_dir():
        raise SystemExit(f"Путь не папка (path is not a directory): {root}")

    for p in root.rglob(pattern):
        if not p.is_file():
            continue

        try:
            text = p.read_text(encoding=encoding, errors=errors_mode)
        except (OSError, UnicodeError):
            # OSError = ошибка ввода/вывода (I/O error)
            # UnicodeError = ошибка декодирования (decode error)
            if args.ignore_errors:
                continue
            raise

        if needle in text:
            print(p)


if __name__ == "__main__":
    main()
