from __future__ import annotations

import argparse
import functools
import re
import subprocess
import tempfile
from typing import Sequence

from all_repos import autofix_lib
from all_repos.config import Config
from all_repos.grep import repos_matching

REF_RE = re.compile('^( +- +uses: +)([^@]+)@[^\r\n]+(.*)$', re.DOTALL)
FMT = '{}{}@{}{}'


def _clone(repo: str, path: str) -> None:
    subprocess.check_call(('git', 'init', '-q', path))
    subprocess.check_call((
        'git', '-C', path, 'config', 'extensions.partialClone', 'true',
    ))
    url = f'https://github.com/{repo}'
    subprocess.check_call(('git', 'remote', 'add', 'origin', url), cwd=path)
    fetch = (
        'git', 'fetch', '--quiet', '--filter=blob:none', '--tags',
        'origin', 'HEAD',
    )
    subprocess.check_call(fetch, cwd=path)


@functools.lru_cache(maxsize=None)
def _latest_tag(repo: str) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        _clone(repo, tmpdir)
        cmd = ('git', 'describe', 'FETCH_HEAD', '--tags', '--abbrev=0')
        return subprocess.check_output(cmd, cwd=tmpdir).strip().decode()


def find_repos(config: Config) -> set[str]:
    query = ('uses:.*@', '--', '.github/')
    return repos_matching(config, query)


def apply_fix() -> None:
    cmd = ('git', 'grep', '-l', 'uses:.*@', '--', '.github')
    for fname in subprocess.check_output(cmd).decode().splitlines():
        with open(fname) as f:
            contents = f.read()

        lines = contents.splitlines(True)
        for i, line in enumerate(lines):
            match = REF_RE.match(line)
            if match is not None:
                tag = _latest_tag(match[2])
                lines[i] = FMT.format(match[1], match[2], tag, match[3])

            with open(fname, 'w') as f:
                f.writelines(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Update github actions versions',
        branch_name='gha-autoupdate',
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
