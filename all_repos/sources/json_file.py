import collections
import json
from typing import Dict


Settings = collections.namedtuple('Settings', ('output_dir', 'filename'))


def output_dir(settings: Settings) -> str:
    return settings.output_dir


def list_repos(settings: Settings) -> Dict[str, str]:
    with open(settings.filename) as f:
        return json.load(f)
