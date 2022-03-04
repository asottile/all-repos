from __future__ import annotations

from typing import NamedTuple

from all_repos import bitbucket_server_api
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    token: str
    base_url: str
    project: str | None = None

    @property
    def auth_header(self) -> dict[str, str]:
        return {'Authorization': f'Bearer {self.token}'}

    def __repr__(self) -> str:
        return hide_api_key_repr(self, key='token')


def list_repos(settings: Settings) -> dict[str, str]:
    return bitbucket_server_api.list_repos(
        settings.base_url,
        settings.auth_header,
        settings.project,
    )
