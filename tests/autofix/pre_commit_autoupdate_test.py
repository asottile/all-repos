import os.path
from unittest import mock

from all_repos.autofix.pre_commit_autoupdate import tmp_pre_commit_home


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
