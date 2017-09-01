import os.path
import subprocess
from unittest import mock

import pytest

from all_repos import clone
from all_repos.autofix.pre_commit_autoupdate import find_repos
from all_repos.autofix.pre_commit_autoupdate import main
from all_repos.autofix.pre_commit_autoupdate import tmp_pre_commit_home
from all_repos.config import load_config
from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo
from testing.git import revparse
from testing.git import write_file_commit


def test_tmp_pre_commit_home_existing_env_variable():
    with mock.patch.dict(os.environ, {'PRE_COMMIT_HOME': '/'}, clear=True):
        with tmp_pre_commit_home():
            tmp_home = os.environ['PRE_COMMIT_HOME']
            assert tmp_home != '/'
            assert os.path.exists(tmp_home)
        assert os.environ['PRE_COMMIT_HOME'] == '/'
        assert not os.path.exists(tmp_home)


def test_tmp_pre_commit_home_no_env_variable():
    with mock.patch.dict(os.environ, clear=True):
        with tmp_pre_commit_home():
            assert os.path.exists(os.environ['PRE_COMMIT_HOME'])
        assert 'PRE_COMMIT_HOME' not in os.environ


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
        f'    sha: {rev}\n'
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
        consuming_repo=consuming_repo,
        update_repo=update_repo,
    )


def test_main(file_config, autoupdatable):
    ret = main((
        '--config-filename', str(file_config.cfg),
        '--repos', str(autoupdatable.update_repo),
    ))
    assert not ret

    ret = autoupdatable.consuming_repo.join('.pre-commit-config.yaml').read()
    assert ret == (
        f'-   repo: {autoupdatable.hook_repo}\n'
        f'    sha: v1\n'
        f'    hooks:\n'
        f'    -   id: hook\n'
    )


def test_find_repos_none(file_config_files):
    assert find_repos(load_config(str(file_config_files.cfg))) == set()


def test_find_repos_finds_a_repo(file_config_files):
    write_file_commit(file_config_files.dir1, '.pre-commit-config.yaml', '[]')
    clone.main(('--config-filename', str(file_config_files.cfg)))
    ret = find_repos(load_config(str(file_config_files.cfg)))
    assert ret == {str(file_config_files.output_dir.join('repo1'))}
