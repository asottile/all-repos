from __future__ import annotations

import subprocess
from unittest import mock

import pytest

from all_repos import clone
from all_repos.autofix import _pre_commit_hook_migrate
from all_repos.autofix import pre_commit_flake8_migrate
from all_repos.autofix.pre_commit_flake8_migrate import find_repos
from all_repos.autofix.pre_commit_flake8_migrate import main
from all_repos.config import load_config
from testing import git
from testing.auto_namedtuple import auto_namedtuple


@pytest.fixture
def fake_autoupdatable(tmpdir):
    repo = tmpdir.join('autoupdatable')
    update_repo = tmpdir.join('autoupdatable_clone')
    git.init_repo(repo)

    def init(contents):
        repo.join('.pre-commit-config.yaml').write(contents)
        git.commit(repo)
        subprocess.check_call(('git', 'clone', repo, update_repo))

    with mock.patch.object(_pre_commit_hook_migrate, 'autoupdate'):
        with mock.patch.object(pre_commit_flake8_migrate, 'check_fix'):
            yield auto_namedtuple(
                init=init, repo=repo, update_repo=update_repo,
            )


def test_apply_fix_noop(file_config, fake_autoupdatable):
    fake_autoupdatable.init('repos: []')
    ret = main((
        '--config-filename', str(file_config.cfg),
        '--repos', str(fake_autoupdatable.update_repo),
    ))
    assert not ret

    contents = fake_autoupdatable.repo.join('.pre-commit-config.yaml').read()
    assert contents == 'repos: []'


def test_replaces_flake8(file_config, fake_autoupdatable):
    before = '''\
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v1.4.0-1
    hooks:
    -   id: trailing-whitespace
    -   id: flake8
    -   id: end-of-file-fixer
-   repo: https://github.com/asottile/reorder_python_imports
    rev: v1.1.0
    hooks:
    -   id: reorder-python-imports
'''
    fake_autoupdatable.init(before)

    ret = main((
        '--config-filename', str(file_config.cfg),
        '--repos', str(fake_autoupdatable.update_repo),
    ))
    assert not ret

    contents = fake_autoupdatable.repo.join('.pre-commit-config.yaml').read()
    assert contents == '''\
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v1.4.0-1
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
-   repo: https://gitlab.com/pycqa/flake8
    rev: 3.7.0
    hooks:
    -   id: flake8
-   repo: https://github.com/asottile/reorder_python_imports
    rev: v1.1.0
    hooks:
    -   id: reorder-python-imports
'''


def test_find_repos_finds_a_repo(file_config_files):
    contents = '''\
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v1.4.0-1
    hooks:
    -   id: flake8
'''
    git.write_file_commit(
        file_config_files.dir1, '.pre-commit-config.yaml', contents,
    )
    clone.main(('--config-filename', str(file_config_files.cfg)))
    ret = find_repos(load_config(str(file_config_files.cfg)))
    assert ret == {str(file_config_files.output_dir.join('repo1'))}


def test_find_repos_does_not_find_migrated_repo(file_config_files):
    contents = '''\
-   repo: https://gitlab.com/pycqa/flake8
    rev: 3.7.0
    hooks:
    -   id: flake8
'''
    git.write_file_commit(
        file_config_files.dir1, '.pre-commit-config.yaml', contents,
    )
    clone.main(('--config-filename', str(file_config_files.cfg)))
    ret = find_repos(load_config(str(file_config_files.cfg)))
    assert ret == set()
