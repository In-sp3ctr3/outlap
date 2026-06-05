from __future__ import annotations

import argparse
import json

from raceweek.core.optimizer import optimize_recommendations
from raceweek.core.projections import run_projection
from raceweek.settings import settings
from raceweek.storage.demo import get_state, reset_state


def main() -> None:
    parser = argparse.ArgumentParser(prog="raceweek")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("demo")
    subparsers.add_parser("seed-demo")
    backtest = subparsers.add_parser("backtest")
    backtest.add_argument("--season", default="2026")
    backtest.add_argument("--strategy", default="balanced")
    args = parser.parse_args()

    if args.command == "seed-demo":
        state = reset_state()
        print(
            json.dumps(
                {
                    "status": "seeded",
                    "databasePath": settings.database_path,
                    "assets": len(state.assets),
                    "sourceSnapshotIds": sorted(state.source_snapshot_ids),
                },
                indent=2,
            )
        )
        return

    state = get_state()
    projection_run = run_projection(state.assets, event_id=state.current_event_id)
    recommendation = optimize_recommendations(
        team=state.team,
        assets=state.assets,
        projections=projection_run.projections,
        event_id=state.current_event_id,
        strategy_mode=args.strategy if args.command == "backtest" else "balanced",
        locked_asset_ids=[],
        banned_asset_ids=[],
        allowed_chips=[],
        max_options=3,
        projection_run_id=projection_run.projection_run_id,
        source_snapshot_ids=projection_run.source_snapshot_ids,
    )
    payload = {
        "command": args.command,
        "season": getattr(args, "season", "2026"),
        "strategy": getattr(args, "strategy", "balanced"),
        "meanAbsoluteErrorDemo": 4.2,
        "topOptions": [
            option.model_dump(by_alias=True)
            for option in recommendation.options[:3]
        ],
    }
    print(json.dumps(payload, indent=2, default=str))
