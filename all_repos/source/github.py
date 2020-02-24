from typing import Dict
from typing import NamedTuple

from all_repos import github_api


class Settings(NamedTuple):
    api_key: str
    username: str
    collaborator: bool
    forks: bool
    private: bool
    archived: bool
    base_url: str


Settings.__new__.__defaults__ = (
    False, False, False, False, 'https://api.github.com',
)


def list_repos(settings: Settings) -> Dict[str, str]:
    repos = github_api.get_all(
        f'{settings.base_url}/user/repos?per_page=100',
        headers={'Authorization': f'token {settings.api_key}'},
    )
    return github_api.filter_repos(
        repos,
        forks=settings.forks,
        private=settings.private,
        collaborator=settings.collaborator,
        archived=settings.archived,
    )
