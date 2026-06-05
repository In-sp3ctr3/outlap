from __future__ import annotations

import json
import sys

import pytest

from raceweek.cli import main


def test_backtest_cli_emits_real_projection_metrics(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "argv", ["raceweek", "backtest"])

    main()

    payload = json.loads(capsys.readouterr().out)
    assert payload["modelName"] == "transparent_weighted_demo"
    assert payload["sampleCount"] > 0
    assert payload["meanAbsoluteError"] > 0
    assert "meanAbsoluteErrorDemo" not in payload
