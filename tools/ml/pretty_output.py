from __future__ import annotations

from typing import Any, Sequence


# ---------- Pretty table utilities ----------


def to_str(v: Any) -> str:
    """
    Stringify values; None -> empty string. 
    Floats compact via .6g for readability.
    """
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.6g}"
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(to_str(x) for x in v) + "]"
    return str(v)


def is_number_like(v: Any) -> bool:
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, str):
        try:
            float(v)
            return True
        except ValueError:
            return False
    return False


def compute_col_widths(
    header: Sequence[str],
    rows: Sequence[Sequence[Any]],
    min_width: int = 3,
    max_width: int = 64,
) -> list[int]:
    n_cols = len(header)
    widths = [len(h) for h in header]
    for row in rows:
        for j in range(n_cols):
            cell = to_str(row[j]) if j < len(row) else ""
            widths[j] = max(widths[j], len(cell))
    return [max(min_width, min(w, max_width)) for w in widths]


def format_row(
    cells: Sequence[Any],
    widths: Sequence[int],
    numeric_mask: Sequence[bool],
) -> str:
    formatted = []
    for j, w in enumerate(widths):
        s = to_str(cells[j]) if j < len(cells) else ""
        if len(s) > w:
            s = s[: max(0, w - 1)] + "…"
        if numeric_mask[j]:
            formatted.append(f"{s:>{w}}")
        else:
            formatted.append(f"{s:<{w}}")
    return " | ".join(formatted)


def print_table(header: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    widths = compute_col_widths(header, rows)
    numeric_mask: list[bool] = []
    for j in range(len(header)):
        numeric_count = 0
        total = 0
        for r in rows:
            if j < len(r):
                total += 1
                if is_number_like(r[j]):
                    numeric_count += 1
        numeric_mask.append(numeric_count > total / 2 if total > 0 else False)
    header_line = " | ".join(f"{h:<{w}}" for h, w in zip(header, widths))
    sep_line = "-+-".join("-" * w for w in widths)
    print(header_line)
    print(sep_line)
    for r in rows:
        print(format_row(r, widths, numeric_mask))
