import argparse
import collections
import contextlib
import json
import multiprocessing
import os.path
import re
import shutil
import subprocess
from typing import Dict


Config = collections.namedtuple('Config', ('output_dir', 'repo_sources'))
RepoSource = collections.namedtuple(
    'RepoSource', ('mod', 'settings', 'include', 'exclude'),
)
RepoSource.__new__.__defaults__ = ('', '^$')


def _to_repo_source(source: dict) -> RepoSource:
    mod = __import__(source['mod'], fromlist=['__trash'])
    settings = mod.Settings(**source['settings'])
    include = re.compile(source.get('include', ''))
    exclude = re.compile(source.get('exclude', '^$'))
    return RepoSource(mod, settings, include, exclude)


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

    sources = tuple(_to_repo_source(x) for x in contents['repo_sources'])
    return Config(
        output_dir=contents['output_dir'],
        repo_sources=sources,
    )


def _git_remote(path: str) -> str:
    return subprocess.check_output((
        'git', '-C', path, 'config', 'remote.origin.url',
    )).decode().strip()


def _get_current_state_helper(path):
    pths = []
    seen_git = False
    for direntry in os.scandir(path):
        if direntry.name == '.git':
            seen_git = True
        elif direntry.is_dir():
            pths.append(direntry)
    if seen_git:
        yield path, _git_remote(path)
    else:
        for pth in pths:
            yield from _get_current_state_helper(pth)


def _get_current_state(path: str) -> Dict[str, str]:
    return {
        os.path.relpath(k, path): v for k, v in _get_current_state_helper(path)
    }


def _remove(dest: str, path: str) -> None:
    print(f'Removing {path}')
    shutil.rmtree(os.path.join(dest, path))


def _init(dest: str, path: str, remote: str) -> None:
    print(f'Initializing {path}')
    path = os.path.join(dest, path)
    os.makedirs(path, exist_ok=True)
    subprocess.check_call(('git', 'init', path))
    subprocess.check_output((
        'git', '-C', path, 'remote', 'add',
        'origin', remote, '--track', 'master',
    ))


def _fetch_reset(path: str) -> None:
    try:
        subprocess.check_call(('git', '-C', path, 'fetch'))
        subprocess.check_call((
            'git', '-C', path, 'reset', '--hard', 'origin/master',
        ))
    except subprocess.CalledProcessError:
        # TODO: color / tty
        print(f'Error fetching {path}')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-C', '--config-filename', default='all-repos.json')
    args = parser.parse_args(argv)

    config = load_config(args.config_filename)
    os.makedirs(config.output_dir, exist_ok=True)
    for source in config.repo_sources:
        output_dir = source.mod.output_dir(source.settings)
        repos = source.mod.list_repos(source.settings)
        repos_filtered = {
            k: v for k, v in repos.items()
            if source.include.search(k) and not source.exclude.search(k)
        }

        dest = os.path.join(config.output_dir, output_dir)
        os.makedirs(dest, exist_ok=True)

        # If the previous `repos.json` / `repos_filtered.json` files exist
        # remove them.
        for f in ('repos.json', 'repos_filtered.json'):
            path = os.path.join(dest, 'repos.json')
            if os.path.exists(path):
                os.remove(path)

        current_repos = set(_get_current_state(dest).items())
        filtered_repos = set(repos_filtered.items())

        # Remove old no longer cloned repositories
        for path, _ in current_repos - filtered_repos:
            _remove(dest, path)

        for path, remote in filtered_repos - current_repos:
            _init(dest, path, remote)

        todo = [os.path.join(dest, p) for p in repos_filtered]
        with contextlib.closing(multiprocessing.Pool(8)) as pool:
            pool.map(_fetch_reset, todo, chunksize=4)

        # TODO: write these last
        with open(os.path.join(dest, 'repos.json'), 'w') as f:
            f.write(json.dumps(repos))
        with open(os.path.join(dest, 'repos_filtered.json'), 'w') as f:
            f.write(json.dumps(repos_filtered))


if __name__ == '__main__':
    exit(main())
