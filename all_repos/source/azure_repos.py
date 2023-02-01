from __future__ import annotations

import base64
import json
import urllib.request
from typing import NamedTuple

from all_repos.util import hide_api_key_repr
from all_repos.util import load_api_key


class Settings(NamedTuple):
    organization: str
    project: str
    base_url: str = 'https://dev.azure.com'
    api_key: str | None = None
    api_key_env: str | None = None

    def __repr__(self) -> str:
        return hide_api_key_repr(self)

    @property
    def auth(self) -> str:
        value = f':{load_api_key(self)}'
        return base64.b64encode(value.encode()).decode()


def list_repos(settings: Settings) -> dict[str, str]:
    url = (
        f'{settings.base_url}/{settings.organization}/{settings.project}/'
        '_apis/git/repositories?api-version=6.0'
    )
    resp = urllib.request.urlopen(
        urllib.request.Request(
            url, headers={'Authorization': f'Basic {settings.auth}'},
        ),
    )
    obj = json.load(resp)
    return {repo['name']: repo['sshUrl'] for repo in obj['value']}
