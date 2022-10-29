from __future__ import annotations

import argparse
import os
from typing import Sequence

from all_repos import autofix_lib
from all_repos.config import Config


def find_repos(config: Config) -> set[str]:
    return set()  # require repos to be specified on the commandline


def apply_fix() -> None:
    try:
        os.remove('.github/FUNDING.yml')
    except OSError:
        pass


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    msg = 'Use org-default .github/FUNDING.yml'

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg=msg,
        branch_name='gh-funding-default',
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
    exit(main())
