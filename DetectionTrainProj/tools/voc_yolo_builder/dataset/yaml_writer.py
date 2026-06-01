"""Ultralytics data.yaml writer."""

from __future__ import annotations

from pathlib import Path


def quote_yaml_string(value: str) -> str:
    """Return a single-quoted YAML string with escaped single quotes."""
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def write_data_yaml(
    output_dir: Path,
    names: list[str],
    include_test: bool = False,
) -> None:
    """Write Ultralytics data.yaml."""
    yaml_path = output_dir / "data.yaml"

    lines: list[str] = [
        f"path: {quote_yaml_string(output_dir.as_posix())}",
        f"train: {quote_yaml_string('images/train')}",
        f"val: {quote_yaml_string('images/val')}",
    ]

    if include_test:
        lines.append(f"test: {quote_yaml_string('images/test')}")

    lines.append("names:")
    for class_id, class_name in enumerate(names):
        lines.append(f"  {class_id}: {quote_yaml_string(class_name)}")

    yaml_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
