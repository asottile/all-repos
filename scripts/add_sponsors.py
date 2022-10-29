from __future__ import annotations

import argparse
import os
from typing import Sequence

from all_repos import autofix_lib
from all_repos.config import Config


def find_repos(config: Config) -> set[str]:
    return set()  # require repos to be specified on the commandline


def apply_fix() -> None:
    os.makedirs('.github', exist_ok=True)
    with open('.github/FUNDING.yml', 'w') as f:
        f.write('github: asottile\n')
    autofix_lib.run('git', 'add', '--intent-to-add', '.github')


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    msg = '''\
Add link to GitHub Sponsors

at the time of writing I am currently unemployed.  I'd love to make open
source a full time career.  if you or your company is deriving value from
this free software, please consider [sponsoring].

[sponsoring]: https://github.com/sponsors/asottile
'''

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg=msg,
        branch_name='gh-sponsors',
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
