from typing import Dict
from typing import NamedTuple

from all_repos import gitlab_api
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    api_key: str
    org: str
    base_url: str = 'https://gitlab.com/api/v4'
    archived: bool = False

    def __repr__(self) -> str:
        return hide_api_key_repr(self)


LIST_REPOS_URL = (
    '{settings.base_url}/groups/'
    '{settings.org}/projects?with_shared=False'
)


def list_repos(settings: Settings) -> Dict[str, str]:
    repos = gitlab_api.get_all(
        LIST_REPOS_URL.format(settings=settings),
        headers={'Private-Token': settings.api_key},
    )
    return gitlab_api.filter_repos_from_settings(repos, settings)
