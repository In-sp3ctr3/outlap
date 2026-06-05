from __future__ import annotations

import hashlib
import json

from raceweek.core.models import OptimizerRequestContext, StrategyMode
from raceweek.core.strategy import normalize_custom_weights


def build_request_context(
    *,
    team_snapshot_id: str,
    event_id: str,
    projection_run_id: str,
    strategy_mode: StrategyMode,
    locked_asset_ids: list[str],
    banned_asset_ids: list[str],
    allowed_chips: list[str],
    custom_weights: dict[str, float] | None,
    max_options: int,
    idempotency_key: str | None,
) -> OptimizerRequestContext:
    return OptimizerRequestContext(
        team_snapshot_id=team_snapshot_id,
        event_id=event_id,
        projection_run_id=projection_run_id,
        strategy_mode=strategy_mode,
        locked_asset_ids=sorted(set(locked_asset_ids)),
        banned_asset_ids=sorted(set(banned_asset_ids)),
        allowed_chips=sorted(set(allowed_chips)),
        custom_weights=normalize_custom_weights(custom_weights or {}),
        max_options=max_options,
        idempotency_key_hash=hash_idempotency_key(idempotency_key),
    )


def fingerprint_request_context(context: OptimizerRequestContext) -> str:
    payload = context.model_dump(by_alias=True, mode="json")
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def hash_idempotency_key(idempotency_key: str | None) -> str | None:
    if not idempotency_key:
        return None
    return hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()
