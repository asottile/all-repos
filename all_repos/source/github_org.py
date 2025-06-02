from __future__ import annotations

from typing import NamedTuple

from all_repos import github_api
from all_repos.util import hide_api_key_repr
from all_repos.util import load_api_key


class Settings(NamedTuple):
    org: str
    collaborator: bool = True
    forks: bool = False
    private: bool = False
    archived: bool = False
    base_url: str = 'https://api.github.com'
    api_key: str | None = None
    api_key_env: str | None = None
    ssh: bool = True

    # TODO: https://github.com/python/mypy/issues/8543
    def __repr__(self) -> str:
        return hide_api_key_repr(self)


def list_repos(settings: Settings) -> dict[str, str]:
    repos = github_api.get_all(
        f'{settings.base_url}/orgs/{settings.org}/repos?per_page=100',
        headers={'Authorization': f'token {load_api_key(settings)}'},
    )
    return github_api.filter_repos(
        repos,
        ssh=settings.ssh,
        forks=settings.forks,
        private=settings.private,
        collaborator=settings.collaborator,
        archived=settings.archived,
    )
