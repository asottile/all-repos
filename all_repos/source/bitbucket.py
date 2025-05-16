from __future__ import annotations

import base64
from typing import NamedTuple

from all_repos import bitbucket_api
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    username: str
    app_password: str
    query: str = ''
    include_workspace: bool = True

    @property
    def auth(self) -> str:
        value = f'{self.username}:{self.app_password}'
        return base64.b64encode(value.encode()).decode()

    # TODO: https://github.com/python/mypy/issues/8543
    def __repr__(self) -> str:
        return hide_api_key_repr(self, key='app_password')


def list_repos(settings: Settings) -> dict[str, str]:
    repos = bitbucket_api.get_all(
        f'https://api.bitbucket.org/2.0/repositories?pagelen=100&role=member&q={settings.query}',
        headers={'Authorization': f'Basic {settings.auth}'},
    )

    path_name_key = 'full_name' if settings.include_workspace else 'slug'
    return {
        repo[path_name_key]: 'git@bitbucket.org:{}.git'.format(repo['full_name'])
        for repo in repos
    }
