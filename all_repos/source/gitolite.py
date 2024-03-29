from __future__ import annotations

import json
import subprocess
from typing import NamedTuple


class Settings(NamedTuple):
    username: str
    hostname: str
    mirror_path: str | None = None

    def clone_url(self, repo_name: str) -> str:
        return (
            self.mirror_path or
            f'{self.username}@{self.hostname}:{{repo_name}}'
        ).format(repo_name=repo_name)


def _repo_names_from_source(settings: Settings) -> set[str]:
    info = subprocess.check_output(
        ('ssh', f'{settings.username}@{settings.hostname}', 'info', '-json'),
    )
    info_d = json.loads(info.decode('UTF-8'))
    return set(info_d['repos'])


def list_repos(settings: Settings) -> dict[str, str]:
    return {
        # Repo names have ".git" appended to avoid naming conflicts between
        # repos and directories in the gitolite hierarchy (a path could
        # otherwise be both).
        f'{repo_name}.git': settings.clone_url(repo_name)
        for repo_name in _repo_names_from_source(settings)
    }
