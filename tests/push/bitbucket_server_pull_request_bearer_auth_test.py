from __future__ import annotations

import json
import subprocess

from all_repos.push.bitbucket_server_pull_request_bearer_auth import push
from all_repos.push.bitbucket_server_pull_request_bearer_auth import Settings


def _resource_json():
    with open('testing/resources/bitbucket/push.json') as f:
        return json.load(f)


def test_bitbucket_server_pull_request(
        mock_urlopen, make_fake_bitbucket_repo,
):
    fake_bitbucket_repo = make_fake_bitbucket_repo(
        Settings('token', 'bitbucket.domain.com'),
    )
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
    settings = Settings('token', 'bitbucket.domain.com')
    assert repr(settings) == (
        'Settings(\n'
        '    token=...,\n'
        "    base_url='bitbucket.domain.com',\n"
        ')'
    )
