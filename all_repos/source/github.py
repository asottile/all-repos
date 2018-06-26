from typing import Dict
from typing import NamedTuple

from all_repos import github_api


class Settings(NamedTuple):
    api_key: str
    username: str
    collaborator: bool = False
    forks: bool = False  # noqa: E701 fixed in flake8>=3.6
    private: bool = False


def list_repos(settings: Settings) -> Dict[str, str]:
    repos = github_api.get_all(
        'https://api.github.com/user/repos?per_page=100',
        headers={'Authorization': f'token {settings.api_key}'},
    )
    return {
        repo['full_name']: 'git@github.com:{}'.format(repo['full_name'])
        for repo in repos
        if (
            (settings.forks or not repo['fork']) and
            (settings.private or not repo['private']) and
            (settings.collaborator or repo['permissions']['admin'])
        )
    }
