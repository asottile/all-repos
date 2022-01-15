from __future__ import annotations

import os.path
from unittest import mock

from all_repos import clone
from all_repos.autofix.pre_commit_autoupdate import find_repos
from all_repos.autofix.pre_commit_autoupdate import main
from all_repos.autofix.pre_commit_autoupdate import tmp_pre_commit_home
from all_repos.config import load_config
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


def test_main(file_config, autoupdatable):
    ret = main((
        '--config-filename', str(file_config.cfg),
        '--repos', str(autoupdatable.update_repo),
    ))
    assert not ret

    ret = autoupdatable.consuming_repo.join('.pre-commit-config.yaml').read()
    assert ret == (
        f'repos:\n'
        f'-   repo: {autoupdatable.hook_repo}\n'
        f'    rev: v1\n'
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
