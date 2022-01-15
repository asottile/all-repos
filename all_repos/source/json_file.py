from __future__ import annotations

import json
from typing import NamedTuple


class Settings(NamedTuple):
    filename: str


def list_repos(settings: Settings) -> dict[str, str]:
    with open(settings.filename) as f:
        return json.load(f)
