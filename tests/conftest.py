import json
import sys
from unittest import mock

import pytest
import requests

from all_repos import clone
from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo
from testing.git import write_file_commit


@pytest.fixture
def mock_requests():
    with mock.patch.object(requests, 'get') as get_mock:
        with mock.patch.object(requests, 'post') as post_mock:
            yield auto_namedtuple(get=get_mock, post=post_mock)


@pytest.fixture
def file_config(tmpdir):
    dir1 = tmpdir.join('1')
    dir2 = tmpdir.join('2')
    rev1 = init_repo(dir1)
    rev2 = init_repo(dir2)

    repos_json = tmpdir.join('repos.json')
    repos_json.write(json.dumps({'repo1': str(dir1), 'repo2': str(dir2)}))

    cfg = tmpdir.join('config.json')
    cfg.write(json.dumps({
        'output_dir': 'output',
        'source': 'all_repos.source.json_file',
        'source_settings': {'filename': str(repos_json)},
        'push': 'all_repos.push.merge_to_master',
        'push_settings': {},
    }))
    cfg.chmod(0o600)
    return auto_namedtuple(
        output_dir=tmpdir.join('output'),
        cfg=cfg,
        repos_json=repos_json,
        dir1=dir1,
        dir2=dir2,
        rev1=rev1,
        rev2=rev2,
    )


@pytest.fixture
def file_config_files(file_config):
    write_file_commit(file_config.dir1, 'f', 'OHAI\n')
    write_file_commit(file_config.dir2, 'f', 'OHELLO\n')
    write_file_commit(file_config.dir2, 'f2', '')
    clone.main(('--config-filename', str(file_config.cfg)))
    return file_config


@pytest.fixture(autouse=True)
def not_a_tty():
    with mock.patch.object(sys.stdout, 'isatty', return_value=False) as mck:
        yield mck
