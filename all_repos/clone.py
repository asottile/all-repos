import argparse
import collections
import contextlib
import functools
import json
import multiprocessing
import os.path
import re
import shutil
import subprocess
from typing import Dict


Config = collections.namedtuple(
    'Config', ('output_dir', 'mod', 'settings', 'include', 'exclude'),
)


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

    mod = __import__(contents['mod'], fromlist=['__trash'])
    settings = mod.Settings(**contents['settings'])
    include = re.compile(contents.get('include', ''))
    exclude = re.compile(contents.get('exclude', '^$'))
    return Config(
        output_dir=contents['output_dir'],
        mod=mod,
        settings=settings,
        include=include,
        exclude=exclude,
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


def jobs_type(s):
    jobs = int(s)
    if jobs <= 0:
        return multiprocessing.cpu_count()
    else:
        return jobs


@contextlib.contextmanager
def in_process_mapper():
    yield map


@contextlib.contextmanager
def pool_mapper(jobs):
    with multiprocessing.Pool(jobs) as pool:
        yield functools.partial(pool.map, chunksize=4)


def get_mapper(jobs):
    if jobs == 1:
        return in_process_mapper()
    else:
        return pool_mapper(jobs)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-C', '--config-filename', default='all-repos.json')
    parser.add_argument('-j', '--jobs', type=jobs_type, default=8)
    args = parser.parse_args(argv)

    config = load_config(args.config_filename)
    os.makedirs(config.output_dir, exist_ok=True)

    repos = config.mod.list_repos(config.settings)
    repos_filtered = {
        k: v for k, v in repos.items()
        if config.include.search(k) and not config.exclude.search(k)
    }

    os.makedirs(config.output_dir, exist_ok=True)

    # If the previous `repos.json` / `repos_filtered.json` files exist
    # remove them.
    repos_f = os.path.join(config.output_dir, 'repos.json')
    repos_filtered_f = os.path.join(config.output_dir, 'repos_filtered.json')
    for path in (repos_f, repos_filtered_f):
        if os.path.exists(path):
            os.remove(path)

    current_repos = set(_get_current_state(config.output_dir).items())
    filtered_repos = set(repos_filtered.items())

    # Remove old no longer cloned repositories
    for path, _ in current_repos - filtered_repos:
        _remove(config.output_dir, path)

    for path, remote in filtered_repos - current_repos:
        _init(config.output_dir, path, remote)

    todo = [os.path.join(config.output_dir, p) for p in repos_filtered]
    with get_mapper(args.jobs) as mapper:
        tuple(mapper(_fetch_reset, todo))

    # TODO: write these last
    with open(repos_f, 'w') as f:
        f.write(json.dumps(repos))
    with open(repos_filtered_f, 'w') as f:
        f.write(json.dumps(repos_filtered))


if __name__ == '__main__':
    exit(main())
