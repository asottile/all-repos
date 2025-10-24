from __future__ import annotations

import urllib.parse
from typing import NamedTuple

from all_repos import gitlab_api
from all_repos.util import hide_api_key_repr
from all_repos.util import load_api_key


class Settings(NamedTuple):
    org: str
    base_url: str = 'https://gitlab.com/api/v4'
    archived: bool = False
    api_key: str | None = None
    api_key_env: str | None = None

    def __repr__(self) -> str:
        return hide_api_key_repr(self)


LIST_REPOS_URL = (
    '{base_url}/groups/'
    '{org}/projects?with_shared=False&include_subgroups=true'
)


def list_repos(settings: Settings) -> dict[str, str]:
    org_escaped = urllib.parse.quote(settings.org, safe='')
    repos = gitlab_api.get_all(
        LIST_REPOS_URL.format(base_url=settings.base_url, org=org_escaped),
        headers={'Private-Token': load_api_key(settings)},
    )
    return gitlab_api.filter_repos_from_settings(repos, settings)
