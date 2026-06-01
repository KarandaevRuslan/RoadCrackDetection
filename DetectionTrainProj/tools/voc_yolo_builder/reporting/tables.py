"""Console output helpers."""

from typing import Any, Iterable, Sequence


DEFAULT_MIN_COLUMN_WIDTH = 3
DEFAULT_MAX_COLUMN_WIDTH = 64


def to_str(value: Any) -> str:
    """Convert a table cell value to a compact printable string."""
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(to_str(item) for item in value) + "]"
    return str(value)


def is_number_like(value: Any) -> bool:
    """Return True when a value should be right-aligned as a number."""
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value)
            return True
        except ValueError:
            return False
    return False


def compute_col_widths(
    header: Sequence[Any],
    rows: Sequence[Sequence[Any]],
    min_width: int = DEFAULT_MIN_COLUMN_WIDTH,
    max_width: int = DEFAULT_MAX_COLUMN_WIDTH,
) -> list[int]:
    """Compute bounded display widths for each table column."""
    column_count = len(header)
    widths = [len(to_str(column_name)) for column_name in header]

    for row in rows:
        for column_index in range(column_count):
            cell = to_str(row[column_index]) if column_index < len(row) else ""
            widths[column_index] = max(widths[column_index], len(cell))

    return [max(min_width, min(width, max_width)) for width in widths]


def format_row(
    cells: Sequence[Any],
    widths: Sequence[int],
    numeric_mask: Sequence[bool],
) -> str:
    """Format a single table row using computed widths and alignment."""
    formatted_cells: list[str] = []

    for column_index, width in enumerate(widths):
        value = to_str(cells[column_index]
                       ) if column_index < len(cells) else ""
        if len(value) > width:
            value = value[: max(0, width - 1)] + "…"

        if numeric_mask[column_index]:
            formatted_cells.append(f"{value:>{width}}")
        else:
            formatted_cells.append(f"{value:<{width}}")

    return " | ".join(formatted_cells)


def build_numeric_mask(
    header: Sequence[Any],
    rows: Sequence[Sequence[Any]],
) -> list[bool]:
    """Infer which columns are mostly numeric and should be right-aligned."""
    numeric_mask: list[bool] = []

    for column_index in range(len(header)):
        numeric_count = 0
        total_count = 0

        for row in rows:
            if column_index >= len(row):
                continue
            total_count += 1
            if is_number_like(row[column_index]):
                numeric_count += 1

        numeric_mask.append(
            numeric_count > total_count / 2 if total_count > 0 else False
        )

    return numeric_mask


def print_table(
    header: Sequence[object],
    rows: Iterable[Sequence[object]]
) -> None:
    """Print an aligned table with compact values, truncation, and numeric alignment."""
    header_values = list(header)
    row_values = [list(row) for row in rows]

    widths = compute_col_widths(header_values, row_values)
    numeric_mask = build_numeric_mask(header_values, row_values)

    header_line = " | ".join(
        f"{to_str(column_name):<{width}}"
        for column_name, width in zip(header_values, widths)
    )
    separator_line = "-+-".join("-" * width for width in widths)

    print(header_line)
    print(separator_line)
    for row in row_values:
        print(format_row(row, widths, numeric_mask))
