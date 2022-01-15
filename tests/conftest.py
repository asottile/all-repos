from __future__ import annotations

import builtins
import json
import subprocess
import sys
import urllib.request
from unittest import mock

import pytest

from all_repos import clone
from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo
from testing.git import write_file_commit


@pytest.fixture
def mock_urlopen():
    with mock.patch.object(urllib.request, 'urlopen') as mck:
        yield mck


@pytest.fixture
def file_config(tmpdir):
    dir1 = tmpdir.join('1')
    dir2 = tmpdir.join('2')
    rev1 = init_repo(dir1)
    rev2 = init_repo(dir2)

    repos_json = tmpdir.join('repos.json')
    repos_json.write(json.dumps({'repo1': str(dir1), 'repo2': str(dir2)}))

    cfg = tmpdir.join('config.json')
    cfg.write(
        json.dumps({
            'output_dir': 'output',
            'source': 'all_repos.source.json_file',
            'source_settings': {'filename': str(repos_json)},
            'push': 'all_repos.push.merge_to_master',
            'push_settings': {},
        }),
    )
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
def file_config_non_default(file_config):
    subprocess.check_call((
        'git', '-C', file_config.dir1, 'branch', '--move', 'm2',
    ))
    subprocess.check_call((
        'git', '-C', file_config.dir1, 'symbolic-ref', 'HEAD', 'refs/heads/m2',
    ))
    write_file_commit(file_config.dir1, 'f', 'OHAI\n')
    return file_config


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


@pytest.fixture
def mock_input():
    class MockInput:
        def __init__(self, mck):
            self.mck = mck

        def set_side_effect(self, *inputs):
            it = iter(inputs)

            def side_effect(s):
                print(s, end='')
                ret = next(it)
                if ret in (EOFError, KeyboardInterrupt):
                    print({EOFError: '^D', KeyboardInterrupt: '^C'}[ret])
                    raise ret
                else:
                    print(f'<<{ret}')
                    return ret

            self.mck.side_effect = side_effect

    with mock.patch.object(builtins, 'input') as mck:
        yield MockInput(mck)
