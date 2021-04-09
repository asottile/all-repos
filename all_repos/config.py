import json
import os
import re
import sys
from typing import Any
from typing import Callable
from typing import Dict
from typing import NamedTuple
from typing import Pattern


class Config(NamedTuple):
    output_dir: str
    include: Pattern[str]
    exclude: Pattern[str]
    list_repos: Callable[[Any], Dict[str, str]]
    source_settings: Any
    push: Callable[[Any, str], None]
    push_settings: Any
    all_branches: bool

    def _path(self, *paths: str) -> str:
        return os.path.abspath(os.path.join(self.output_dir, *paths))

    @property
    def repos_path(self) -> str:
        return self._path('repos.json')

    @property
    def repos_filtered_path(self) -> str:
        return self._path('repos_filtered.json')

    def get_cloned_repos(self) -> Dict[str, str]:
        with open(self.repos_filtered_path) as f:
            return json.load(f)


def _check_permissions(filename: str) -> None:
    mode = os.stat(filename).st_mode & 0o777
    if sys.platform != 'win32' and mode != 0o600:
        raise SystemExit(
            f'{filename} has too-permissive permissions, Expected 0o600, '
            f'got 0o{mode:o}',
        )


def load_config(filename: str) -> Config:
    _check_permissions(filename)
    with open(filename) as f:
        contents = json.load(f)

    output_dir = os.path.join(filename, '..', contents['output_dir'])
    output_dir = os.path.normpath(output_dir)
    source_module: Any = __import__(contents['source'], fromlist=['__trash'])
    source_settings = source_module.Settings(**contents['source_settings'])
    push_module: Any = __import__(contents['push'], fromlist=['__trash'])
    push_settings = push_module.Settings(**contents['push_settings'])
    include = re.compile(contents.get('include', ''))
    exclude = re.compile(contents.get('exclude', '^$'))
    all_branches = contents.get('all_branches', False)
    return Config(
        output_dir=output_dir, include=include, exclude=exclude,
        list_repos=source_module.list_repos, source_settings=source_settings,
        push=push_module.push, push_settings=push_settings,
        all_branches=all_branches,
    )
