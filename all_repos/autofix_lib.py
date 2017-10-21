import collections
import contextlib
import functools
import os
import pipes
import subprocess
import tempfile
import traceback

import pkg_resources

from all_repos import cli
from all_repos import color
from all_repos import git
from all_repos import mapper
from all_repos.config import Config
from all_repos.config import load_config


def add_fixer_args(parser):
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


class Commit(collections.namedtuple(
        'Commit', ('msg', 'branch_name', 'author'),
)):
    __slots__ = ()

    @classmethod
    def from_cli(cls, args, *, msg, branch_name):
        return cls(msg=msg, branch_name=branch_name, author=args.author)


class AutofixSettings(collections.namedtuple(
        'AutofixSettings',
        ('jobs', 'color', 'limit', 'dry_run', 'interactive'),
)):
    __slots__ = ()

    @classmethod
    def from_cli(cls, args):
        return cls(
            jobs=args.jobs, color=args.color, limit=args.limit,
            dry_run=args.dry_run, interactive=args.interactive,
        )


def filter_repos(config, cli_repos, find_repos):
    if cli_repos is not None:
        return cli_repos
    else:
        return find_repos(config)


def from_cli(args, *, find_repos, msg, branch_name):
    config = load_config(args.config_filename)
    return (
        filter_repos(config, args.repos, find_repos),
        config,
        Commit.from_cli(args, msg=msg, branch_name=branch_name),
        AutofixSettings.from_cli(args),
    )


def run(*cmd, **kwargs):
    cmdstr = ' '.join(pipes.quote(arg) for arg in cmd)
    print(f'$ {cmdstr}', flush=True)
    kwargs.setdefault('check', True)
    return subprocess.run(cmd, **kwargs)


@contextlib.contextmanager
def cwd(path):
    pwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(pwd)


def assert_importable(module: str, *, install: str) -> None:
    try:
        __import__(module)
    except ImportError:
        raise SystemExit(
            f'This tool requires the `{module}` module to be installed.\n'
            f'Try installing it via `pip install {install}`.',
        )


def require_version_gte(pkg_name: str, version: str) -> None:
    pkg = pkg_resources.get_distribution(pkg_name)
    pkg_version = pkg_resources.parse_version(pkg.version)
    target_version = pkg_resources.parse_version(version)
    if pkg_version < target_version:
        raise SystemExit(
            f'This tool requires the `{pkg_name}` package is at least version '
            f'{version}.  '
            f'The currently installed version is {pkg.version}.\n\n'
            f'Try `pip install --upgrade {pkg_name}`',
        )


@contextlib.contextmanager
def repo_context(repo, *, use_color):
    print(color.fmt(f'***{repo}', color.TURQUOISE_H, use_color=use_color))
    try:
        remote = git.remote(repo)
        with tempfile.TemporaryDirectory() as tmpdir:
            run('git', 'clone', '--quiet', repo, tmpdir)
            with cwd(tmpdir):
                run('git', 'remote', 'set-url', 'origin', remote)
                run('git', 'fetch', '--prune')
                yield
    except Exception:
        print(color.fmt(f'***Errored', color.RED_H, use_color=use_color))
        traceback.print_exc()


def _interactive_check(*, use_color):
    def _quit():
        print('Goodbye!')
        raise SystemExit()

    while True:
        try:
            s = input(color.fmt(
                '***Looks good [y,n,s,q,?]? ',
                color.BLUE_B, use_color=use_color,
            ))
        except (EOFError, KeyboardInterrupt):
            _quit()

        s = s.strip().lower()
        if s in {'y', 'yes'}:
            return True
        elif s in {'n', 'no'}:
            return False
        elif s in {'s', 'shell'}:
            print('Opening an interactive shell, type `exit` to continue.')
            print('Any modifications will be committed.')
            subprocess.call(os.environ.get('SHELL', 'bash'))
        elif s in {'q', 'quit'}:
            _quit()
        else:
            if s not in {'?', 'help'}:
                print(color.fmt(
                    f'Unexpected input: {s}', color.RED, use_color=use_color,
                ))
            print('y (yes): yes it looks good, commit and continue.')
            print('n (no): no, do not commit this repository.')
            print('s (shell): open an interactive shell in the repo.')
            print('q (quit, ^C): early exit from the autofixer.')
            print('? (help): show this help message.')


def _fix_inner(repo, apply_fix, check_fix, config, commit, autofix_settings):
    with repo_context(repo, use_color=autofix_settings.color):
        branch_name = f'all-repos_autofix_{commit.branch_name}'
        run('git', 'checkout', '--quiet', 'origin/master', '-b', branch_name)

        apply_fix()

        diff = run('git', 'diff', 'origin/master', '--exit-code', check=False)
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
        commit_cmd = ('git', 'commit', '--quiet', '-a', '-m', commit_message)
        if commit.author:
            commit_cmd += ('--author', commit.author)

        run(*commit_cmd)

        if autofix_settings.dry_run:
            return

        config.push(config.push_settings, branch_name)


def _noop_check_fix():
    """A lambda is not pickleable, this must be a module-level function"""


def fix(
        repos, *,
        apply_fix,
        check_fix=_noop_check_fix,
        config: Config,
        commit: Commit,
        autofix_settings: AutofixSettings,
):
    assert not autofix_settings.interactive or autofix_settings.jobs == 1
    repos = tuple(repos)[:autofix_settings.limit]
    func = functools.partial(
        _fix_inner,
        apply_fix=apply_fix, check_fix=check_fix,
        config=config, commit=commit, autofix_settings=autofix_settings,
    )
    with mapper.process_mapper(autofix_settings.jobs) as do_map:
        mapper.exhaust(do_map(func, repos))
