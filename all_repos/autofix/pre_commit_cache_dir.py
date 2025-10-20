from __future__ import annotations

import argparse
import os.path
from collections.abc import Sequence

from all_repos import autofix_lib
from all_repos.config import Config
from all_repos.grep import repos_matching

REPLACES = (
    (
        'appveyor.yml',
        r'%USERPROFILE%\.pre-commit',
        r'%USERPROFILE%\.cache\pre-commit',
    ),
    (
        '.travis.yml',
        '$HOME/.pre-commit',
        '$HOME/.cache/pre-commit',
    ),
)


def find_repos(config: Config) -> set[str]:
    return {
        repo
        for fname, pattern, _ in REPLACES
        for repo in repos_matching(config, ('-F', pattern, '--', fname))
    }


def _replace_if_exists(filename: str, s1: str, s2: str) -> None:
    if os.path.exists(filename):
        with open(filename) as f:
            contents = f.read()
        contents = contents.replace(s1, s2)
        with open(filename, 'w') as f:
            f.write(contents)


def apply_fix() -> None:
    for fname, find, replace in REPLACES:
        _replace_if_exists(fname, find, replace)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Update pre-commit cache directory',
        branch_name='pre-commit-cache-dir',
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
