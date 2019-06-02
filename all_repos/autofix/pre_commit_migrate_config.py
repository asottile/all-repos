import argparse
import os.path
import sys
from typing import Optional
from typing import Sequence
from typing import Set

import yaml
from pre_commit.constants import CONFIG_FILE

from all_repos import autofix_lib
from all_repos.autofix.pre_commit_autoupdate import check_fix
from all_repos.autofix.pre_commit_autoupdate import find_repos as _find_repos
from all_repos.autofix.pre_commit_autoupdate import tmp_pre_commit_home
from all_repos.config import Config


def apply_fix() -> None:
    autofix_lib.run(sys.executable, '-m', 'pre_commit', 'migrate-config')


def _has_legacy_config(repo_dir: str) -> bool:
    with open(os.path.join(repo_dir, CONFIG_FILE)) as f:
        contents = yaml.safe_load(f.read())
    return isinstance(contents, list)


def find_repos(config: Config) -> Set[str]:
    return {repo for repo in _find_repos(config) if _has_legacy_config(repo)}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    autofix_lib.assert_importable('pre_commit', install='pre-commit')
    # pre-commit 1.0.0: introduces migrate-config
    # pre-commit 1.0.1: exit code fix
    # pre-commit 1.7.0: sha -> rev
    autofix_lib.require_version_gte('pre-commit', '1.7.0')

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Run pre-commit migrate-config',
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
    return 0


if __name__ == '__main__':
    exit(main())
