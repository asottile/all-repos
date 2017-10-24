import collections
import json
import os
import re


class Config(collections.namedtuple(
        'Config',
        (
            'output_dir', 'include', 'exclude',
            'list_repos', 'source_settings',
            'push', 'push_settings',
        ),
)):
    __slots__ = ()

    def _path(self, *paths):
        return os.path.abspath(os.path.join(self.output_dir, *paths))

    @property
    def repos_path(self):
        return self._path('repos.json')

    @property
    def repos_filtered_path(self):
        return self._path('repos_filtered.json')

    def get_cloned_repos(self):
        with open(self.repos_filtered_path) as f:
            return json.load(f)


def _check_permissions(filename: str) -> None:
    mode = os.stat(filename).st_mode & 0o777
    if mode != 0o600:
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
    source_module = __import__(contents['source'], fromlist=['__trash'])
    source_settings = source_module.Settings(**contents['source_settings'])
    push_module = __import__(contents['push'], fromlist=['__trash'])
    push_settings = push_module.Settings(**contents['push_settings'])
    include = re.compile(contents.get('include', ''))
    exclude = re.compile(contents.get('exclude', '^$'))
    return Config(
        output_dir=output_dir, include=include, exclude=exclude,
        list_repos=source_module.list_repos, source_settings=source_settings,
        push=push_module.push, push_settings=push_settings,
    )
