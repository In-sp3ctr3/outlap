from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass
from typing import Any

from raceweek.connectors.import_template_contracts import (
    HEADER_ALIASES,
    REQUIRED_COLUMNS,
)
from raceweek.core.models import (
    ImportPreviewRequest,
    ImportPreviewResponse,
    ImportValidationMessage,
    TemplateType,
)


@dataclass(frozen=True)
class ParsedTemplate:
    preview: ImportPreviewResponse
    event_id: str | None


def parse_template(request: ImportPreviewRequest) -> ParsedTemplate:
    content_hash = _hash_text(request.raw_text)
    delimiter = _detect_delimiter(request.raw_text)
    reader = csv.DictReader(io.StringIO(request.raw_text), delimiter=delimiter)
    detected_headers = [header.strip() for header in reader.fieldnames or []]
    mapped_headers = _mapped_headers(detected_headers)
    messages = _header_messages(request.template_type, mapped_headers)
    rows: list[dict[str, Any]] = []
    event_id: str | None = None

    for offset, raw_row in enumerate(reader, start=2):
        canonical = _canonical_row(raw_row, mapped_headers)
        row, row_messages = _normalize_row(request.template_type, canonical, offset)
        rows.append(row)
        messages.extend(row_messages)
        event_id = event_id or _event_id(canonical)

    if not rows:
        messages.append(
            ImportValidationMessage(
                severity="error",
                message="CSV must include at least one data row.",
                suggested_fix="Add rows below the header.",
            )
        )

    return ParsedTemplate(
        preview=ImportPreviewResponse(
            template_type=request.template_type,
            inferred_delimiter=delimiter,
            detected_headers=detected_headers,
            mapped_headers=mapped_headers,
            rows=rows,
            messages=messages,
            importable=not any(message.severity == "error" for message in messages),
            content_hash=content_hash,
            row_count=len(rows),
        ),
        event_id=event_id,
    )


def _normalize_row(
    template_type: TemplateType,
    row: dict[str, str],
    row_number: int,
) -> tuple[dict[str, Any], list[ImportValidationMessage]]:
    messages = _row_required_messages(template_type, row, row_number)
    normalized: dict[str, Any]
    if template_type == "market_prices":
        normalized = {
            "assetId": row.get("asset_id")
            or _asset_id(row.get("asset_kind"), row.get("asset_name")),
            "assetType": _asset_type(row.get("asset_kind")),
            "displayName": _clean_name(row.get("asset_name")),
            "shortName": _optional_clean(row.get("short_name")),
            "constructorName": _optional_clean(row.get("team_name")),
            "teamColor": _optional_color(row.get("team_color")),
            "priceMillions": _positive_float(row.get("price_m"), row_number, "price_m", messages),
            "fantasyPoints": _optional_float(row.get("fantasy_points_total")),
            "ownershipPct": _optional_percent(row.get("selection_percent")),
            "selectedByPct": _optional_percent(row.get("selection_percent")),
        }
    elif template_type == "team_state":
        normalized = {
            "eventId": _event_id(row),
            "slot": _optional_int(row.get("slot_number")),
            "teamName": _clean_name(row.get("team_name")),
            "costCapMillions": _positive_float(
                row.get("cost_cap_m"),
                row_number,
                "cost_cap_m",
                messages,
            ),
            "budgetUsedMillions": _optional_float(row.get("budget_used_m")),
            "budgetRemainingMillions": _non_negative_float(
                row.get("bank_m"),
                row_number,
                "bank_m",
                messages,
            ),
            "freeTransfers": _non_negative_int(
                row.get("free_transfers"),
                row_number,
                "free_transfers",
                messages,
            ),
            "transferPenaltyPoints": _optional_float(row.get("transfer_penalty_points")),
            "totalPoints": _optional_float(row.get("total_points")),
        }
    elif template_type == "team_slots":
        normalized = {
            "eventId": _event_id(row),
            "assetId": row.get("asset_id")
            or _asset_id(row.get("asset_kind") or row.get("slot_type"), row.get("asset_name")),
            "assetType": _asset_type(row.get("asset_kind") or row.get("slot_type")),
            "slotNumber": _non_negative_int(
                row.get("slot_number"),
                row_number,
                "slot_number",
                messages,
            ),
            "displayName": _clean_name(row.get("asset_name")),
            "boostMultiplier": _optional_float(row.get("boost_multiplier")),
        }
    elif template_type == "fantasy_scores":
        normalized = {
            "eventId": _event_id(row),
            "assetId": row.get("asset_id")
            or _asset_id(row.get("asset_kind"), row.get("asset_name")),
            "assetType": _asset_type(row.get("asset_kind") or "driver"),
            "displayName": _clean_name(row.get("asset_name")),
            "fantasyPoints": _required_float(
                row.get("fantasy_points_total"),
                row_number,
                "fantasy_points_total",
                messages,
            ),
        }
    elif template_type == "league_table":
        normalized = {
            "eventId": _event_id(row),
            "leagueId": row.get("league_id") or None,
            "leagueName": _optional_clean(row.get("league_name")),
            "leagueRank": _non_negative_int(
                row.get("league_rank"),
                row_number,
                "league_rank",
                messages,
            ),
            "teamName": _clean_name(row.get("team_name")),
            "totalPoints": _required_float(
                row.get("total_points"),
                row_number,
                "total_points",
                messages,
            ),
            "roundPoints": _optional_float(row.get("round_points")),
            "managerName": _optional_clean(row.get("manager_name")),
            "assetIds": _split_asset_ids(row.get("asset_ids")),
        }
    elif template_type == "chips_state":
        normalized = {
            "eventId": _event_id(row),
            "slot": _optional_int(row.get("slot_number")),
            "chipName": _clean_name(row.get("chip_name")).lower(),
            "status": _chip_status(row.get("chip_status")),
            "usedEventId": _optional_clean(row.get("used_event_id")),
            "sourceNote": _optional_clean(row.get("source_note")),
        }
    elif template_type == "season_totals":
        normalized = {
            "eventId": _event_id(row),
            "slot": _optional_int(row.get("slot_number")),
            "teamName": _clean_name(row.get("team_name")),
            "totalPoints": _required_float(
                row.get("total_points"),
                row_number,
                "total_points",
                messages,
            ),
            "overallRank": _optional_int(row.get("overall_rank")),
            "leagueRank": _optional_int(row.get("league_rank")),
            "sourceNote": _optional_clean(row.get("source_note")),
        }
    elif template_type == "transfer_history_optional":
        normalized = {
            "eventId": _event_id(row),
            "slot": _optional_int(row.get("slot_number")),
            "transferNumber": _non_negative_int(
                row.get("transfer_number"),
                row_number,
                "transfer_number",
                messages,
            ),
            "outAssetId": _optional_clean(row.get("out_asset_id")),
            "outDisplayName": _optional_clean(row.get("out_display_name")),
            "inAssetId": _optional_clean(row.get("in_asset_id")),
            "inDisplayName": _optional_clean(row.get("in_display_name")),
            "penaltyPoints": _optional_float(row.get("penalty_points")),
            "chipActive": _optional_clean(row.get("chip_active")),
            "sourceNote": _optional_clean(row.get("source_note")),
        }
    else:
        normalized = {
            "eventId": _event_id(row),
            "leagueId": row.get("league_id"),
            "teamName": _clean_name(row.get("team_name")),
            "leagueRank": _optional_int(row.get("league_rank")),
            "assetId": row.get("asset_id")
            or _asset_id(row.get("asset_kind"), row.get("asset_name")),
            "assetType": _asset_type(row.get("asset_kind")),
            "displayName": _clean_name(row.get("asset_name")),
            "constructorName": _optional_clean(row.get("team_name")),
            "sourceNote": _optional_clean(row.get("source_note")),
        }
    return normalized, messages


def _header_messages(
    template_type: TemplateType,
    mapped_headers: dict[str, str],
) -> list[ImportValidationMessage]:
    missing = sorted(REQUIRED_COLUMNS[template_type] - set(mapped_headers))
    return [
        ImportValidationMessage(
            column=column,
            severity="error",
            message=f"Missing required column: {column}.",
            suggested_fix=f"Add a {column} column to this template.",
        )
        for column in missing
    ]


def _row_required_messages(
    template_type: TemplateType,
    row: dict[str, str],
    row_number: int,
) -> list[ImportValidationMessage]:
    messages: list[ImportValidationMessage] = []
    for column in sorted(REQUIRED_COLUMNS[template_type]):
        if row.get(column) in {None, ""}:
            messages.append(
                ImportValidationMessage(
                    row_number=row_number,
                    column=column,
                    severity="error",
                    message=f"{column} is required.",
                    suggested_fix=f"Enter a value for {column}.",
                )
            )
    return messages


def _mapped_headers(headers: list[str]) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for header in headers:
        normalized = _normalize_header(header)
        canonical = next(
            (name for name, aliases in HEADER_ALIASES.items() if normalized in aliases),
            normalized,
        )
        mapped[canonical] = header
    return mapped


def _canonical_row(
    raw_row: dict[str, str | None],
    mapped_headers: dict[str, str],
) -> dict[str, str]:
    return {
        canonical: (raw_row.get(original) or "").strip()
        for canonical, original in mapped_headers.items()
    }


def _detect_delimiter(raw_text: str) -> str:
    sample = raw_text[:2048]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t;").delimiter
    except csv.Error:
        counts = {delimiter: sample.count(delimiter) for delimiter in [",", "\t", ";"]}
        return max(counts, key=lambda delimiter: counts[delimiter])


def _event_id(row: dict[str, str]) -> str | None:
    explicit = row.get("event_id")
    if explicit:
        return explicit
    season = row.get("season")
    round_number = row.get("round")
    if not season or not round_number:
        return None
    try:
        return f"event_{int(season)}_{int(round_number):02d}"
    except ValueError:
        return None


def _asset_type(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized in {"constructor", "constructors", "team", "c"}:
        return "constructor"
    return "driver"


def _asset_id(kind: str | None, name: str | None) -> str:
    return f"asset_{_asset_type(kind)}_{_slug(name or 'unknown')}"


def _clean_name(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _optional_clean(value: str | None) -> str | None:
    cleaned = _clean_name(value)
    return cleaned or None


def _optional_color(value: str | None) -> str | None:
    cleaned = _clean_name(value)
    if not cleaned:
        return None
    color = cleaned if cleaned.startswith("#") else f"#{cleaned}"
    return color if re.fullmatch(r"#[0-9A-Fa-f]{6}", color) else None


def _required_float(
    value: str | None,
    row_number: int,
    column: str,
    messages: list[ImportValidationMessage],
) -> float:
    parsed = _float(value)
    if parsed is None:
        messages.append(_numeric_message(row_number, column))
        return 0
    return parsed


def _positive_float(
    value: str | None,
    row_number: int,
    column: str,
    messages: list[ImportValidationMessage],
) -> float:
    parsed = _required_float(value, row_number, column, messages)
    if parsed <= 0:
        messages.append(
            ImportValidationMessage(
                row_number=row_number,
                column=column,
                severity="error",
                message=f"{column} must be greater than zero.",
                suggested_fix="Use a value like 12.3.",
            )
        )
    return parsed


def _non_negative_float(
    value: str | None,
    row_number: int,
    column: str,
    messages: list[ImportValidationMessage],
) -> float:
    parsed = _required_float(value, row_number, column, messages)
    if parsed < 0:
        messages.append(
            ImportValidationMessage(
                row_number=row_number,
                column=column,
                severity="error",
                message=f"{column} must be non-negative.",
                suggested_fix="Use zero or a positive value.",
            )
        )
    return parsed


def _non_negative_int(
    value: str | None,
    row_number: int,
    column: str,
    messages: list[ImportValidationMessage],
) -> int:
    parsed = _float(value)
    if parsed is None or int(parsed) != parsed:
        messages.append(
            ImportValidationMessage(
                row_number=row_number,
                column=column,
                severity="error",
                message=f"{column} must be a whole number.",
                suggested_fix="Use a value like 2.",
            )
        )
        return 0
    if parsed < 0:
        messages.append(
            ImportValidationMessage(
                row_number=row_number,
                column=column,
                severity="error",
                message=f"{column} must be non-negative.",
            )
        )
    return int(parsed)


def _optional_float(value: str | None) -> float | None:
    return _float(value)


def _optional_int(value: str | None) -> int | None:
    parsed = _float(value)
    if parsed is None or int(parsed) != parsed:
        return None
    return int(parsed)


def _chip_status(value: str | None) -> str:
    normalized = (value or "unknown").strip().lower()
    if normalized == "locked":
        return "unavailable"
    if normalized in {"available", "used", "active", "unavailable", "unknown"}:
        return normalized
    return "unknown"


def _optional_percent(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    stripped = value.strip()
    has_percent = stripped.endswith("%")
    parsed = _float(stripped.removesuffix("%"))
    if parsed is None:
        return None
    return parsed if has_percent or parsed > 1 else parsed * 100


def _float(value: str | None) -> float | None:
    if value in {None, ""}:
        return None
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None


def _numeric_message(row_number: int, column: str) -> ImportValidationMessage:
    return ImportValidationMessage(
        row_number=row_number,
        column=column,
        severity="error",
        message=f"{column} must be numeric.",
        suggested_fix="Use a plain number.",
    )


def _split_asset_ids(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.replace("|", ";").split(";") if item.strip()]


def _normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "unknown"


def _hash_text(raw_text: str) -> str:
    return hashlib.sha256(raw_text.encode()).hexdigest()
