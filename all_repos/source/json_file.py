import json
from typing import Dict
from typing import NamedTuple


class Settings(NamedTuple):
    filename: str


def list_repos(settings: Settings) -> Dict[str, str]:
    with open(settings.filename) as f:
        return json.load(f)
