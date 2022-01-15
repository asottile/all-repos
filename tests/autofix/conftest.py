from __future__ import annotations

import subprocess

import pytest

from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo
from testing.git import revparse


@pytest.fixture
def autoupdatable(tmpdir):
    hook_repo = tmpdir.join('hook_repo')
    init_repo(hook_repo)
    hook_repo.join('.pre-commit-hooks.yaml').write(
        '-   id: hook\n'
        '    name: Hook\n'
        '    entry: echo hi\n'
        '    language: system\n'
        '    types: [file]\n',
    )
    subprocess.check_call(('git', '-C', hook_repo, 'add', '.'))
    subprocess.check_call((
        'git', '-C', hook_repo, 'commit', '-m', 'add hook',
    ))
    rev = revparse(hook_repo)
    subprocess.check_call(('git', '-C', hook_repo, 'tag', 'v1'))

    consuming_repo = tmpdir.join('consuming')
    init_repo(consuming_repo)
    consuming_repo.join('.pre-commit-config.yaml').write(
        f'-   repo: {hook_repo}\n'
        f'    rev: {rev}\n'
        f'    hooks:\n'
        f'    -   id: hook\n',
    )
    subprocess.check_call(('git', '-C', consuming_repo, 'add', '.'))
    subprocess.check_call((
        'git', '-C', consuming_repo, 'commit', '-m', 'consume hook',
    ))

    update_repo = tmpdir.join('update_repo')
    subprocess.check_call(('git', 'clone', consuming_repo, update_repo))

    return auto_namedtuple(
        hook_repo=hook_repo,
        hook_repo_rev=rev,
        consuming_repo=consuming_repo,
        update_repo=update_repo,
    )
