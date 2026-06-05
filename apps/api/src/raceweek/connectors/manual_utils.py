from __future__ import annotations

import csv
import io
from collections import Counter

from raceweek.connectors.manual_types import ManualImportError


def as_dict(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise ManualImportError("manual import payload must be an object")
    return payload


def filter_mapping(
    payload: dict[str, object],
    allowed: set[str],
    label: str,
) -> tuple[dict[str, object], list[str]]:
    unknown = sorted(set(payload) - allowed)
    warnings = [f"{label} ignored unknown fields: {', '.join(unknown)}"] if unknown else []
    return {key: value for key, value in payload.items() if key in allowed}, warnings


def filter_list(
    value: object,
    allowed: set[str],
    label: str,
) -> tuple[list[dict[str, object]], list[str]]:
    if not isinstance(value, list):
        raise ManualImportError(f"{label} must be a list")
    filtered_rows = []
    warnings = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ManualImportError(f"{label}[{index}] must be an object")
        filtered, item_warnings = filter_mapping(item, allowed, f"{label}[{index}]")
        filtered_rows.append(filtered)
        warnings.extend(item_warnings)
    return filtered_rows, warnings


def read_csv_rows(
    body: dict[str, object],
    allowed: set[str],
    label: str,
) -> tuple[list[dict[str, object]], list[str]]:
    content = required_str(body, "content")
    reader = csv.DictReader(io.StringIO(content))
    if reader.fieldnames is None:
        raise ManualImportError(f"{label} must include a header row")
    unknown = sorted(set(reader.fieldnames) - allowed)
    warnings = [f"{label} ignored unknown columns: {', '.join(unknown)}"] if unknown else []
    rows = [
        {key: value for key, value in row.items() if key in allowed and value not in {None, ""}}
        for row in reader
    ]
    if not rows:
        raise ManualImportError(f"{label} must include at least one row")
    return rows, warnings


def required_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if value is None or value == "":
        raise ManualImportError(f"{key} is required")
    return str(value)


def required_float(payload: dict[str, object], key: str) -> float:
    try:
        return float(required_str(payload, key))
    except ValueError as exc:
        raise ManualImportError(f"{key} must be numeric") from exc


def required_int(payload: dict[str, object], key: str) -> int:
    try:
        return int(required_str(payload, key))
    except ValueError as exc:
        raise ManualImportError(f"{key} must be an integer") from exc


def reject_duplicate_ids(values: list[str], label: str) -> None:
    duplicates = [value for value, count in Counter(values).items() if count > 1]
    if duplicates:
        raise ManualImportError(f"duplicate {label} IDs: {', '.join(sorted(duplicates))}")


def split_asset_ids(value: str) -> list[str]:
    return [asset_id.strip() for asset_id in value.replace("|", ";").split(";") if asset_id.strip()]


def default_chips() -> list[dict[str, str]]:
    return [
        {"chipName": "wildcard", "status": "available"},
        {"chipName": "limitless", "status": "available"},
        {"chipName": "no_negative", "status": "available"},
        {"chipName": "autopilot", "status": "available"},
        {"chipName": "3x_boost", "status": "available"},
        {"chipName": "final_fix", "status": "available"},
    ]
