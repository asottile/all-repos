import argparse
import contextlib
import os
import sys
import tempfile

from all_repos import autofix_lib
from all_repos.grep import repos_matching


@contextlib.contextmanager
def tmp_pre_commit_home(*, _absent=object()):
    """During lots of autoupdates, many repositories will be cloned into the
    pre-commit directory.  This prevents leaving many MB/GB of repositories
    behind due to this autofixer.  This context creates a temporary directory
    so these many repositories are automatically cleaned up.
    """
    before = os.environ.get('PRE_COMMIT_HOME', _absent)
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['PRE_COMMIT_HOME'] = tmpdir
        try:
            yield
        finally:
            if before is _absent:
                os.environ.pop('PRE_COMMIT_HOME', None)
            else:
                os.environ['PRE_COMMIT_HOME'] = before


def _run_all_files(**kwargs):
    autofix_lib.run(
        sys.executable, '-m', 'pre_commit', 'run', '--all-files', **kwargs,
    )


def find_repos(config):
    return repos_matching(config, ('', '--', '.pre-commit-config.yaml'))


def apply_fix():
    autofix_lib.run(sys.executable, '-m', 'pre_commit', 'autoupdate')
    # This may return nonzero for fixes, that's ok!
    _run_all_files(check=False)


def check_fix():
    _run_all_files()


def main(argv=None):
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    autofix_lib.assert_importable('pre_commit', install='pre-commit')
    # pre-commit 0.16.3: autoupdate maintains formatting better
    # pre-commit 0.17.0: race conditions in pre-commit install fixed
    # pre-commit 1.0.0: migrate_config(...) is called for autoupdate
    # pre-commit 1.0.1: exit code fix
    autofix_lib.require_version_gte('pre-commit', '1.0.1')

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Ran pre-commit autoupdate.', branch_name='pre-commit-autoupdate',
    )

    with tmp_pre_commit_home():
        autofix_lib.fix(
            repos,
            apply_fix=apply_fix,
            check_fix=check_fix,
            config=config,
            commit=commit,
            autofix_settings=autofix_settings,
        )


if __name__ == '__main__':
    exit(main())
