from __future__ import annotations

import argparse
import contextlib
import functools
import importlib.metadata
import os
import shlex
import subprocess
import sys
import tempfile
import traceback
from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Iterable
from typing import Any
from typing import NamedTuple
from typing import NoReturn

from packaging.version import Version

from all_repos import cli
from all_repos import color
from all_repos import git
from all_repos import mapper
from all_repos.config import Config
from all_repos.config import load_config

if sys.version_info >= (3, 11):  # pragma: >=3.11 cover
    from contextlib import chdir
else:  # pragma: <3.11 cover
    from contextlib_chdir import chdir


def add_fixer_args(parser: argparse.ArgumentParser) -> None:
    cli.add_common_args(parser)

    mutex = parser.add_mutually_exclusive_group()
    mutex.add_argument(
        '--dry-run', action='store_true',
        help='show what would happen but do not push.',
    )
    mutex.add_argument(
        '-i', '--interactive', action='store_true',
        help='interactively approve / deny fixes.',
    )
    cli.add_jobs_arg(mutex, default=1)

    parser.add_argument(
        '--limit', type=int, default=None,
        help='maximum number of repos to process (default: unlimited).',
    )
    parser.add_argument(
        '--author',
        help=(
            'override commit author.  '
            'This is passed directly to `git commit`.  '
            "An example: `--author='Herp Derp <herp.derp@umich.edu>'`."
        ),
    )
    parser.add_argument(
        '--repos', nargs='*',
        help=(
            'run against specific repositories instead.  This is especially '
            'useful with `xargs autofixer ... --repos`.  This can be used to '
            'specify repositories which are not managed by `all-repos`.'
        ),
    )


class Commit(NamedTuple):
    msg: str
    branch_name: str
    author: str | None


class AutofixSettings(NamedTuple):
    jobs: int
    color: bool
    limit: int | None
    dry_run: bool
    interactive: bool

    @classmethod
    def from_cli(cls, args: Any) -> AutofixSettings:
        return cls(
            jobs=args.jobs, color=args.color, limit=args.limit,
            dry_run=args.dry_run, interactive=args.interactive,
        )


def filter_repos(
        config: Config,
        cli_repos: Iterable[str] | None,
        find_repos: Callable[[Config], Iterable[str]],
) -> Iterable[str]:
    if cli_repos is not None:
        return cli_repos
    else:
        return find_repos(config)


def from_cli(
        args: Any,
        *,
        find_repos: Callable[[Config], Iterable[str]],
        msg: str,
        branch_name: str,
) -> tuple[Iterable[str], Config, Commit, AutofixSettings]:
    config = load_config(args.config_filename)
    return (
        filter_repos(config, args.repos, find_repos),
        config,
        Commit(msg=msg, branch_name=branch_name, author=args.author),
        AutofixSettings.from_cli(args),
    )


def run(*cmd: str, **kwargs: Any) -> subprocess.CompletedProcess[str]:
    print(f'$ {shlex.join(cmd)}', flush=True)
    kwargs.setdefault('check', True)
    return subprocess.run(cmd, **kwargs)


def assert_importable(module: str, *, install: str) -> None:
    try:
        __import__(module)
    except ImportError:
        raise SystemExit(
            f'This tool requires the `{module}` module to be installed.\n'
            f'Try installing it via `pip install {install}`.',
        )


def require_version_gte(pkg_name: str, version: str) -> None:
    pkg_version = Version(importlib.metadata.version(pkg_name))
    target_version = Version(version)
    if pkg_version < target_version:
        raise SystemExit(
            f'This tool requires the `{pkg_name}` package is at least version '
            f'{version}.  '
            f'The currently installed version is {pkg_version}.\n\n'
            f'Try `pip install --upgrade {pkg_name}`',
        )


def target_branch() -> str:
    cmd = ('git', 'rev-parse', '--abbrev-ref', '--symbolic', '@{u}')
    out = subprocess.check_output(cmd).strip().decode()
    assert out.startswith('origin/')
    return out[len('origin/'):]


@contextlib.contextmanager
def repo_context(repo: str, *, use_color: bool) -> Generator[None]:
    print(color.fmt(f'***{repo}', color.TURQUOISE_H, use_color=use_color))
    try:
        remote = git.remote(repo)
        with tempfile.TemporaryDirectory() as tmpdir:
            run('git', 'clone', '--quiet', repo, tmpdir)
            with chdir(tmpdir):
                run('git', 'remote', 'set-url', 'origin', remote)
                run('git', 'fetch', '--prune', '--quiet')
                yield
    except Exception:
        print(color.fmt('***Errored', color.RED_H, use_color=use_color))
        traceback.print_exc()


def shell() -> None:
    print('Opening an interactive shell, type `exit` to continue.')
    print('Any modifications will be committed.')
    subprocess.call(os.environ.get('SHELL', 'bash'))


def _interactive_check(*, use_color: bool) -> bool:
    def _quit() -> NoReturn:
        print('Goodbye!')
        raise SystemExit()

    while True:
        try:
            s = input(
                color.fmt(
                    '***Looks good [y,n,s,q,?]? ',
                    color.BLUE_B, use_color=use_color,
                ),
            )
        except (EOFError, KeyboardInterrupt):
            _quit()

        s = s.strip().lower()
        if s in {'y', 'yes'}:
            return True
        elif s in {'n', 'no'}:
            return False
        elif s in {'s', 'shell'}:
            shell()
        elif s in {'q', 'quit'}:
            _quit()
        else:
            if s not in {'?', 'help'}:
                print(
                    color.fmt(
                        f'Unexpected input: {s}',
                        color.RED, use_color=use_color,
                    ),
                )
            print('y (yes): yes it looks good, commit and continue.')
            print('n (no): no, do not commit this repository.')
            print('s (shell): open an interactive shell in the repo.')
            print('q (quit, ^C): early exit from the autofixer.')
            print('? (help): show this help message.')


def _fix_inner(
        repo: str,
        apply_fix: Callable[[], None],
        check_fix: Callable[[], None],
        config: Config,
        commit: Commit,
        autofix_settings: AutofixSettings,
) -> None:
    with repo_context(repo, use_color=autofix_settings.color):
        branch_name = f'all-repos_autofix_{commit.branch_name}'
        run('git', 'checkout', '--quiet', 'origin/HEAD', '-b', branch_name)

        apply_fix()

        diff = run('git', 'diff', 'origin/HEAD', '--exit-code', check=False)
        if not diff.returncode:
            return

        check_fix()

        if (
                autofix_settings.interactive and
                not _interactive_check(use_color=autofix_settings.color)
        ):
            return

        commit_message = (
            f'{commit.msg}\n\n'
            f'Committed via https://github.com/asottile/all-repos'
        )
        commit_cmd: tuple[str, ...] = (
            'git', 'commit', '--quiet', '-a', '-m', commit_message,
        )
        if commit.author:
            commit_cmd += ('--author', commit.author)

        run(*commit_cmd)

        if autofix_settings.dry_run:
            return

        config.push(config.push_settings, branch_name)


def _noop_check_fix() -> None:
    """A lambda is not pickleable, this must be a module-level function"""


def fix(
        repos: Iterable[str],
        *,
        apply_fix: Callable[[], None],
        check_fix: Callable[[], None] = _noop_check_fix,
        config: Config,
        commit: Commit,
        autofix_settings: AutofixSettings,
) -> None:
    assert not autofix_settings.interactive or autofix_settings.jobs == 1
    repos = tuple(repos)[:autofix_settings.limit]
    func = functools.partial(
        _fix_inner,
        apply_fix=apply_fix, check_fix=check_fix,
        config=config, commit=commit, autofix_settings=autofix_settings,
    )
    with mapper.process_mapper(autofix_settings.jobs) as do_map:
        mapper.exhaust(do_map(func, repos))
