from typing import Dict
from typing import NamedTuple

from all_repos import github_api
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    api_key: str
    repo: str
    collaborator: bool = True
    forks: bool = True
    private: bool = False
    archived: bool = False
    base_url: str = 'https://api.github.com'

    # TODO: https://github.com/python/mypy/issues/8543
    def __repr__(self) -> str:
        return hide_api_key_repr(self)


def list_repos(settings: Settings) -> Dict[str, str]:
    repos = []
    to_search = [settings.repo]

    while to_search:
        slug = to_search.pop()
        res = github_api.get_all(
            f'{settings.base_url}/repos/{slug}/forks?per_page=100',
            headers={'Authorization': f'token {settings.api_key}'},
        )
        repos.extend(res)
        to_search.extend(repo['full_name'] for repo in res if repo['forks'])

    return github_api.filter_repos(
        repos,
        forks=settings.forks,
        private=settings.private,
        collaborator=settings.collaborator,
        archived=settings.archived,
    )
