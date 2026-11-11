"""Разбор файлов с планом и фактом показателей (CSV, XLSX).

Обязательные столбцы: kpi (показатель), period (период), plan (план).
Необязательные: fact (факт), unit (единица), direction (higher/lower).
Допустимы русские названия: показатель, период, план, факт, единица, направление.
"""
from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from openpyxl import load_workbook

ALIASES = {
    "kpi": "kpi", "показатель": "kpi",
    "period": "period", "период": "period",
    "plan": "plan", "план": "plan",
    "fact": "fact", "факт": "fact",
    "unit": "unit", "единица": "unit", "ед. изм.": "unit", "ед.изм.": "unit",
    "direction": "direction", "направление": "direction",
}
HIGHER = {"higher", "up", "больше", "рост", "max"}
LOWER = {"lower", "down", "меньше", "снижение", "min"}


class ImportFileError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class ImportRow:
    line: int
    kpi: str
    period: str
    plan: float
    fact: Optional[float]
    unit: str
    higher_is_better: Optional[bool]


def _to_float(value) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        x = float(value)
    else:
        text = str(value).strip().replace("\u00a0", "").replace(" ", "")
        if text == "":
            return None
        x = float(text.replace(",", "."))
    if not math.isfinite(x):
        raise ValueError("не конечное число")
    return x


def _period_to_str(value) -> str:
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m")
    return str(value).strip() if value is not None else ""


def _read_csv(content: bytes) -> list[list]:
    for enc in ("utf-8-sig", "cp1251"):
        try:
            text = content.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ImportFileError(["Не удалось определить кодировку файла (ожидается UTF-8 или CP1251)"])
    first_line = text.splitlines()[0] if text.strip() else ""
    delimiter = ";" if first_line.count(";") >= first_line.count(",") and ";" in first_line else ","
    return [row for row in csv.reader(io.StringIO(text), delimiter=delimiter)]


def _read_xlsx(content: bytes) -> list[list]:
    try:
        wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception as exc:  # повреждённый файл
        raise ImportFileError([f"Не удалось открыть Excel-файл: {exc}"])
    ws = wb.worksheets[0]
    return [list(row) for row in ws.iter_rows(values_only=True)]


def parse_measurements(filename: str, content: bytes) -> list[ImportRow]:
    name = filename.lower()
    if name.endswith(".csv"):
        table = _read_csv(content)
    elif name.endswith(".xlsx"):
        table = _read_xlsx(content)
    else:
        raise ImportFileError(["Поддерживаются файлы .csv и .xlsx"])

    table = [r for r in table if any(c not in (None, "") for c in r)]
    if not table:
        raise ImportFileError(["Файл пуст"])

    header = [ALIASES.get(str(c).strip().lower()) if c is not None else None for c in table[0]]
    missing = [c for c in ("kpi", "period", "plan") if c not in header]
    if missing:
        raise ImportFileError([f"Не найдены обязательные столбцы: {', '.join(missing)}"])
    idx = {col: header.index(col) for col in set(header) if col}

    rows: list[ImportRow] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()

    def cell(raw: list, col: str):
        i = idx.get(col)
        return raw[i] if i is not None and i < len(raw) else None

    for line, raw in enumerate(table[1:], start=2):
        try:
            kpi = str(cell(raw, "kpi") or "").strip()
            period = _period_to_str(cell(raw, "period"))
            if not kpi or not period:
                raise ValueError("пустой показатель или период")
            plan = _to_float(cell(raw, "plan"))
            if plan is None:
                raise ValueError("не указан план")
            fact = _to_float(cell(raw, "fact"))
            unit = str(cell(raw, "unit") or "").strip()
            direction = str(cell(raw, "direction") or "").strip().lower()
            if direction == "":
                hib = None
            elif direction in HIGHER:
                hib = True
            elif direction in LOWER:
                hib = False
            else:
                raise ValueError(f"неизвестное направление «{direction}»")
            if (kpi, period) in seen:
                raise ValueError(f"повтор пары показатель/период: {kpi}, {period}")
            seen.add((kpi, period))
            rows.append(ImportRow(line, kpi, period, plan, fact, unit, hib))
        except ValueError as exc:
            errors.append(f"Строка {line}: {exc}")

    if errors:
        raise ImportFileError(errors)
    return rows
