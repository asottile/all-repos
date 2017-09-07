import argparse
import sys

from all_repos import autofix_lib
from all_repos import cli
from all_repos.autofix.pre_commit_autoupdate import check_fix
from all_repos.autofix.pre_commit_autoupdate import find_repos
from all_repos.autofix.pre_commit_autoupdate import tmp_pre_commit_home


def apply_fix():
    autofix_lib.run(sys.executable, '-m', 'pre_commit', 'migrate-config')


def main(argv=None):
    parser = argparse.ArgumentParser()
    cli.add_fixer_args(parser)
    args = parser.parse_args(argv)

    autofix_lib.assert_importable('pre_commit', install='pre-commit')
    # pre-commit 1.0.0: introduces migrate-config
    # pre-commit 1.0.1: exit code fix
    autofix_lib.require_version_gte('pre-commit', '1.0.1')

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Ran pre-commit migrate-config.',
        branch_name='pre-commit-migrate-config',
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
