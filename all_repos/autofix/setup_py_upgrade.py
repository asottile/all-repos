from __future__ import annotations

import argparse
import sys
from typing import Sequence

from all_repos import autofix_lib
from all_repos.config import Config
from all_repos.grep import repos_matching


def find_repos(config: Config) -> set[str]:
    return repos_matching(config, ('=', '--', 'setup.py'))


def apply_fix() -> None:
    autofix_lib.run(sys.executable, '-m', 'setup_py_upgrade', '.')
    setup_cfg_fmt_cmd = (sys.executable, '-m', 'setup_cfg_fmt', 'setup.cfg')
    autofix_lib.run(*setup_cfg_fmt_cmd, check=False)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    autofix_lib.assert_importable(
        'setup_py_upgrade', install='setup-py-upgrade',
    )
    autofix_lib.assert_importable('setup_cfg_fmt', install='setup-cfg-fmt')

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Migrate setup.py to setup.cfg declarative metadata',
        branch_name='setup-py-upgrade',
    )

    autofix_lib.fix(
        repos,
        apply_fix=apply_fix,
        config=config,
        commit=commit,
        autofix_settings=autofix_settings,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
