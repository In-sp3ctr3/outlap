from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault(
    "RACEWEEK_DATABASE_PATH",
    str(Path(tempfile.gettempdir()) / f"raceweek-tests-{os.getpid()}.duckdb"),
)
