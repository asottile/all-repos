from __future__ import annotations

import json
import subprocess

import pytest

from all_repos.push.bitbucket_server_pull_request import push
from all_repos.push.bitbucket_server_pull_request import Settings
from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo


def _resource_json():
    with open('testing/resources/bitbucket/push.json') as f:
        return json.load(f)


@pytest.fixture
def fake_bitbucket_repo(tmpdir):
    # hax: make the repo end with proj/slug so it "looks" like a bitbucket repo
    src = tmpdir.join('proj/slug')
    init_repo(src)

    dest = tmpdir.join('dest')
    subprocess.check_call(('git', 'clone', src, dest))
    subprocess.check_call((
        'git', '-C', dest, 'checkout', 'origin/master', '-b', 'feature',
    ))
    subprocess.check_call((
        'git', '-C', dest, 'commit', '--allow-empty',
        '-m', 'This is a commit message\n\nHere is some more information!',
    ))
    settings = Settings('user', 'token', 'bitbucket.domain.com')
    return auto_namedtuple(src=src, dest=dest, settings=settings)


def test_bitbucket_server_pull_request(mock_urlopen, fake_bitbucket_repo):
    resp = _resource_json()
    mock_urlopen.return_value.read.return_value = json.dumps(resp).encode()

    with fake_bitbucket_repo.dest.as_cwd():
        push(fake_bitbucket_repo.settings, 'feature')

    # Should have pushed the branch to origin
    out = subprocess.check_output((
        'git', '-C', fake_bitbucket_repo.src, 'branch',
    )).decode()
    assert out == '  feature\n* master\n'

    expected_url = 'https://bitbucket.domain.com/rest/api/1.0/' \
        + 'projects/proj/repos/slug/pull-requests'
    # Pull request should have been made with the commit data
    (req,), _ = mock_urlopen.call_args
    assert req.get_full_url() == expected_url
    assert req.method == 'POST'
    data = json.loads(req.data)
    assert data['title'] == 'This is a commit message'
    assert data['description'] == 'Here is some more information!'
    assert data['fromRef']['id'] == 'feature'


def test_settings_repr():
    settings = Settings('cool_user', 'app_password', 'bitbucket.domain.com')
    assert repr(settings) == (
        'Settings(\n'
        "    username='cool_user',\n"
        '    app_password=...,\n'
        "    base_url='bitbucket.domain.com',\n"
        ')'
    )
