from typing import Dict
from typing import NamedTuple

from all_repos import gitlab_api
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    api_key: str
    org: str
    base_url: str = 'https://gitlab.com/api/v4'
    archived: bool = False
    with_shared: bool = False
    include_subgroups: bool = False

    def __repr__(self) -> str:
        return hide_api_key_repr(self)


def list_repos(settings: Settings) -> Dict[str, str]:
    repos = gitlab_api.get_all(
        f'{settings.base_url}/groups/{settings.org}/projects'
        f'?with_shared={settings.with_shared}'
        f'&include_subgroups={settings.include_subgroups}',
        headers={'Private-Token': settings.api_key},
    )
    return gitlab_api.filter_repos_from_settings(repos, settings)
