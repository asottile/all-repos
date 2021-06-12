import argparse
import functools
import json
import os.path
import shutil
import subprocess
from typing import Dict
from typing import Generator
from typing import Optional
from typing import Sequence
from typing import Tuple

from all_repos import cli
from all_repos import git
from all_repos import mapper
from all_repos.config import load_config


def _get_current_state_helper(
        path: str,
) -> Generator[Tuple[str, str], None, None]:
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
        yield path, git.remote(path)
    else:
        for pth in pths:
            yield from _get_current_state_helper(os.fspath(pth))


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
        'git', '-C', path, 'remote', 'add', 'origin', remote,
    ))


def _default_branch(remote: str) -> str:
    cmd = ('git', 'ls-remote', '--exit-code', '--symref', remote, 'HEAD')
    out = subprocess.check_output(cmd, encoding='UTF-8')
    line = out.splitlines()[0]
    start, end = 'ref: refs/heads/', '\tHEAD'
    assert line.startswith(start) and line.endswith(end), line
    return line[len(start):-1 * len(end)]


def _fetch_reset(path: str, *, all_branches: bool) -> None:
    def _git(*cmd: str) -> None:
        subprocess.check_call(('git', '-C', path, *cmd))

    try:
        branch = _default_branch(git.remote(path))
        if all_branches:
            _git(
                'config', 'remote.origin.fetch',
                '+refs/heads/*:refs/remotes/origin/*',
            )
        else:
            _git('remote', 'set-branches', 'origin', branch)
        _git('fetch', 'origin')
        _git('checkout', branch)
        _git('reset', '--hard', f'origin/{branch}')
    except subprocess.CalledProcessError:
        # TODO: color / tty
        print(f'Error fetching {path}')


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Clone all the repositories into the `output_dir`.  If '
            'run again, this command will update existing repositories.'
        ),
        usage='%(prog)s [options]',
    )
    cli.add_common_args(parser)
    cli.add_jobs_arg(parser)
    args = parser.parse_args(argv)

    config = load_config(args.config_filename)

    repos = config.list_repos(config.source_settings)
    repos_filtered = {
        k: v for k, v in sorted(repos.items())
        if config.include.search(k) and not config.exclude.search(k)
    }

    # If the previous `repos.json` / `repos_filtered.json` files exist
    # remove them.
    for path in (config.repos_path, config.repos_filtered_path):
        if os.path.exists(path):
            os.remove(path)

    current_repos = set(_get_current_state(config.output_dir).items())
    filtered_repos = set(repos_filtered.items())

    # Remove old no longer cloned repositories
    for path, _ in current_repos - filtered_repos:
        _remove(config.output_dir, path)

    for path, remote in filtered_repos - current_repos:
        _init(config.output_dir, path, remote)

    fn = functools.partial(_fetch_reset, all_branches=config.all_branches)
    todo = [os.path.join(config.output_dir, p) for p in repos_filtered]
    with mapper.thread_mapper(args.jobs) as do_map:
        mapper.exhaust(do_map(fn, todo))

    # write these last
    os.makedirs(config.output_dir, exist_ok=True)
    with open(config.repos_path, 'w') as f:
        f.write(json.dumps(repos))
    with open(config.repos_filtered_path, 'w') as f:
        f.write(json.dumps(repos_filtered))
    return 0


if __name__ == '__main__':
    exit(main())
