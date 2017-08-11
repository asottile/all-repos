import json
import subprocess
import sys
from unittest import mock

import pytest

from testing.auto_namedtuple import auto_namedtuple
from testing.git import revparse


def _init_repo(pth):
    subprocess.check_call(('git', 'init', pth))
    subprocess.check_call((
        'git', '-C', pth, 'commit', '--allow-empty', '-m', pth,
    ))
    return revparse(pth)


@pytest.fixture
def file_config(tmpdir):
    dir1 = tmpdir.join('1')
    dir2 = tmpdir.join('2')
    rev1 = _init_repo(dir1)
    rev2 = _init_repo(dir2)

    repos_json = tmpdir.join('repos.json')
    repos_json.write(json.dumps({'repo1': str(dir1), 'repo2': str(dir2)}))

    cfg = tmpdir.join('config.json')
    cfg.write(json.dumps({
        'output_dir': 'output',
        'mod': 'all_repos.sources.json_file',
        'settings': {'filename': str(repos_json)},
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


@pytest.fixture(autouse=True)
def not_a_tty():
    with mock.patch.object(sys.stdout, 'isatty', return_value=False) as mck:
        yield mck
