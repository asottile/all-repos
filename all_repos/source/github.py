from typing import Dict
from typing import NamedTuple

from all_repos import github_api


class Settings(NamedTuple):
    api_key: str
    username: str
    collaborator: bool = False
    forks: bool = False
    private: bool = False


def list_repos(settings: Settings) -> Dict[str, str]:
    repos = github_api.get_all(
        'https://api.github.com/user/repos?per_page=100',
        headers={'Authorization': f'token {settings.api_key}'},
    )
    return github_api.filter_repos(
        repos,
        forks=settings.forks,
        private=settings.private,
        collaborator=settings.collaborator,
    )
