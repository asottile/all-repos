from __future__ import annotations

from typing import NamedTuple

from all_repos.push.bitbucket_server_pull_request import push_and_create_pr
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    token: str
    base_url: str

    @property
    def auth_header(self) -> dict[str, str]:
        return {'Authorization': f'Bearer {self.token}'}

    def __repr__(self) -> str:
        return hide_api_key_repr(self, key='token')


def push(settings: Settings, branch_name: str) -> None:
    push_and_create_pr(settings.base_url, settings.auth_header, branch_name)
