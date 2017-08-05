import argparse
import concurrent.futures
import json
import os.path
import shutil
import subprocess
from typing import Dict

from all_repos import cli
from all_repos.config import load_config


def _git_remote(path: str) -> str:
    return subprocess.check_output((
        'git', '-C', path, 'config', 'remote.origin.url',
    )).decode().strip()


def _get_current_state_helper(path):
    if not os.path.exists(path):
        return

    pths = []
    seen_git = False
    for direntry in os.scandir(path):
        if direntry.name == '.git':
            seen_git = True
        elif direntry.is_dir():  # pragma: no branch (defensive)
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
    # Remove any empty directories
    path = os.path.dirname(path)
    while path and not os.listdir(os.path.join(dest, path)):
        os.rmdir(os.path.join(dest, path))
        path = os.path.dirname(path)


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
    cli.add_config_arg(parser)
    cli.add_jobs_arg(parser)
    args = parser.parse_args(argv)

    config = load_config(args.config_filename)

    repos = config.mod.list_repos(config.settings)
    repos_filtered = {
        k: v for k, v in repos.items()
        if config.include.search(k) and not config.exclude.search(k)
    }

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
    with concurrent.futures.ThreadPoolExecutor(args.jobs) as ex:
        tuple(ex.map(_fetch_reset, todo))

    # TODO: write these last
    with open(repos_f, 'w') as f:
        f.write(json.dumps(repos))
    with open(repos_filtered_f, 'w') as f:
        f.write(json.dumps(repos_filtered))


if __name__ == '__main__':
    exit(main())
