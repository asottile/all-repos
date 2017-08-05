import collections
import json
import os
import re


class Config(collections.namedtuple(
        'Config', ('output_dir', 'mod', 'settings', 'include', 'exclude'),
)):
    __slots__ = ()

    def get_cloned_repos(self):
        repos = os.path.join(self.output_dir, 'repos_filtered.json')
        with open(repos) as f:
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
    mod = __import__(contents['mod'], fromlist=['__trash'])
    settings = mod.Settings(**contents['settings'])
    include = re.compile(contents.get('include', ''))
    exclude = re.compile(contents.get('exclude', '^$'))
    return Config(
        output_dir=output_dir,
        mod=mod,
        settings=settings,
        include=include,
        exclude=exclude,
    )
