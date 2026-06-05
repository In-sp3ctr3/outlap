from __future__ import annotations

import json
from typing import Any


def dump_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def load_json_value(value: Any) -> Any:
    if isinstance(value, str):
        return json.loads(value)
    return value
