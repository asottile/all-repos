import collections
import json
from typing import Dict


Settings = collections.namedtuple('Settings', ('filename',))


def list_repos(settings: Settings) -> Dict[str, str]:
    with open(settings.filename) as f:
        return json.load(f)
