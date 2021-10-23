import argparse
import functools
from typing import Optional
from typing import Sequence
from typing import Set

from all_repos import autofix_lib
from all_repos.autofix._pre_commit_hook_migrate import apply_fix_fn
from all_repos.autofix.pre_commit_autoupdate import check_fix
from all_repos.autofix.pre_commit_autoupdate import tmp_pre_commit_home
from all_repos.config import Config
from all_repos.grep import repos_matching


def find_repos(config: Config) -> Set[str]:
    return repos_matching(
        config, ('autopep8-wrapper', '--', '.pre-commit-config.yaml'),
    )


apply_fix = functools.partial(
    apply_fix_fn,
    prev_hook='autopep8-wrapper',
    repo='https://github.com/pre-commit/mirrors-autopep8',
    rev='v1.4',
    hook='autopep8',
)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    autofix_lib.assert_importable('pre_commit', install='pre-commit')
    autofix_lib.require_version_gte('pre-commit', '1.7.0')

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Migrate from autopep8-wrapper to mirrors-autopep8',
        branch_name='pre-commit-autopep8-migrate',
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
    raise SystemExit(main())
