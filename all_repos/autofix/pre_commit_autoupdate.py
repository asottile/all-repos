import argparse
import contextlib
import os
import sys
import tempfile
from typing import Any
from typing import Generator
from typing import Optional
from typing import Sequence
from typing import Set

from all_repos import autofix_lib
from all_repos.config import Config
from all_repos.grep import repos_matching


@contextlib.contextmanager
def tmp_pre_commit_home() -> Generator[None, None, None]:
    """During lots of autoupdates, many repositories will be cloned into the
    pre-commit directory.  This prevents leaving many MB/GB of repositories
    behind due to this autofixer.  This context creates a temporary directory
    so these many repositories are automatically cleaned up.
    """
    before = os.environ.get('PRE_COMMIT_HOME')
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['PRE_COMMIT_HOME'] = tmpdir
        try:
            yield
        finally:
            if before is None:
                os.environ.pop('PRE_COMMIT_HOME', None)
            else:
                os.environ['PRE_COMMIT_HOME'] = before


def check_fix(**kwargs: Any) -> None:
    autofix_lib.run(
        sys.executable, '-m', 'pre_commit', 'run', '--all-files', **kwargs,
    )


def find_repos(config: Config) -> Set[str]:
    return repos_matching(config, ('', '--', '.pre-commit-config.yaml'))


def apply_fix() -> None:
    autofix_lib.run(sys.executable, '-m', 'pre_commit', 'autoupdate')
    # This may return nonzero for fixes, that's ok!
    check_fix(check=False)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    autofix_lib.assert_importable('pre_commit', install='pre-commit')
    # pre-commit 0.16.3: autoupdate maintains formatting better
    # pre-commit 0.17.0: race conditions in pre-commit install fixed
    # pre-commit 1.0.0: migrate_config(...) is called for autoupdate
    # pre-commit 1.0.1: exit code fix
    # pre-commit 1.7.0: sha -> rev
    autofix_lib.require_version_gte('pre-commit', '1.7.0')

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Run pre-commit autoupdate', branch_name='pre-commit-autoupdate',
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
    return 0


if __name__ == '__main__':
    exit(main())
