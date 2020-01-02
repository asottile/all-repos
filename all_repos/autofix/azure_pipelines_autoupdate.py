import argparse
import functools
import re
import subprocess
import tempfile
from typing import Optional
from typing import Sequence
from typing import Set

import yaml

from all_repos import autofix_lib
from all_repos.config import Config
from all_repos.grep import repos_matching

REF_RE = re.compile('^( +)ref:( *)refs/tags/[^ #\r\n]+(.*)$', re.DOTALL)
FMT = '{}ref:{}refs/tags/{}{}'


def _clone(service: str, repo: str, path: str) -> None:
    assert service == 'github', f'not yet supported {service}'
    subprocess.check_call(('git', 'init', '-q', path))
    url = f'https://github.com/{repo}'
    subprocess.check_call(('git', 'remote', 'add', 'origin', url), cwd=path)
    fetch = ('git', 'fetch', 'origin', 'HEAD', '--tags')
    subprocess.check_call(fetch, cwd=path)


@functools.lru_cache(maxsize=None)
def _latest_tag(service: str, repo: str) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        _clone(service, repo, tmpdir)
        cmd = ('git', 'describe', 'FETCH_HEAD', '--tags', '--abbrev=0')
        return subprocess.check_output(cmd, cwd=tmpdir).strip().decode()


def find_repos(config: Config) -> Set[str]:
    query = ('ref: refs/tags/', '--', 'azure-pipelines.yml')
    return repos_matching(config, query)


def apply_fix() -> None:
    with open('azure-pipelines.yml') as f:
        contents = f.read()
    lines = contents.splitlines(True)
    idxs = [i for i, line in enumerate(lines) if REF_RE.match(line)]
    data = yaml.safe_load(contents)
    targets = [
        repo for repo in data['resources']['repositories']
        if repo['repository'] != 'self'
    ]
    if len(idxs) != len(targets):
        raise AssertionError(f'ref: mismatch {len(idxs)} {len(targets)}')

    for idx, repo in zip(idxs, targets):
        match = REF_RE.match(lines[idx])
        assert match is not None
        tag = _latest_tag(repo['type'], repo['name'])
        lines[idx] = FMT.format(match[1], match[2], tag, match[3])

    with open('azure-pipelines.yml', 'w') as f:
        f.write(''.join(lines))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Update azure-pipelines template repositories',
        branch_name='azure-pipelines-autoupdate',
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
