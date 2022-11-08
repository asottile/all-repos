from __future__ import annotations

import json
import subprocess

import pytest

from all_repos.push import azure_repos_pull_request
from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


@pytest.fixture
def fake_azure_repo(tmpdir):
    # hax: make the repo end with project/slug so it "looks" like an azure repo
    src = tmpdir.join('project/slug')
    init_repo(src)

    dest = tmpdir.join('dest')
    subprocess.check_call(('git', 'clone', src, dest))
    subprocess.check_call((
        'git', '-C', dest, 'checkout', 'origin/HEAD', '-b', 'feature',
    ))
    subprocess.check_call((
        'git', '-C', dest, 'commit', '--allow-empty',
        '-m', 'This is a commit message\n\nHere is some more information!',
    ))
    settings = azure_repos_pull_request.Settings(
        api_key='fake-token',
        organization='fake-org',
        project='fake-project',
    )
    return auto_namedtuple(src=src, dest=dest, settings=settings)


def test_azure_repos_pull_request(mock_urlopen, fake_azure_repo):
    url = (
        'https://dev.azure.com/fake-org/fake-project/'
        '_apis/git/repositories/slug/pullrequests?api-version=6.0'
    )
    resp = {
        'repository':
        {
            'webUrl': 'https://dev.azure.com/fake-org/fake-project/_git/slug',
        },
        'pullRequestId': '101',
    }
    mock_urlopen.side_effect = urlopen_side_effect({
        url: FakeResponse(json.dumps(resp).encode()),
    })
    with fake_azure_repo.dest.as_cwd():
        azure_repos_pull_request.push(fake_azure_repo.settings, 'feature')

    # Should have pushed the branch to origin
    out = subprocess.check_output((
        'git', '-C', fake_azure_repo.src, 'branch',
    )).decode()
    assert out == '  feature\n* main\n'

    # Pull request should have been made with the commit data
    (req,), _ = mock_urlopen.call_args
    assert req.method == 'POST'
    data = json.loads(req.data)
    assert data['title'] == 'This is a commit message'
    assert data['description'] == 'Here is some more information!'
    assert data['sourceRefName'] == 'refs/heads/feature'


def test_settings_repr():
    settings = azure_repos_pull_request.Settings(
        api_key='fake-token',
        organization='fake-org',
        project='fake-project',
    )
    assert repr(settings) == (
        'Settings(\n'
        '    api_key=...,\n'
        "    organization='fake-org',\n"
        "    project='fake-project',\n"
        "    base_url='https://dev.azure.com',\n"
        ')'
    )
