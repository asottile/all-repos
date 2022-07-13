from __future__ import annotations

import json
import subprocess
import urllib

import pytest

from all_repos.push import gitlab_pull_request
from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo


@pytest.fixture
def fake_gitlab_repo(tmpdir):
    # hax: make the repo end with :repo/slug so it "looks" like a gitlab repo
    src = tmpdir.join('repo:user/slug')
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
    settings = gitlab_pull_request.Settings(api_key='fake')
    return auto_namedtuple(src=src, dest=dest, settings=settings)


def test_gitlab_pull_request(mock_urlopen, fake_gitlab_repo):
    resp = {'web_url': 'https://example/com'}
    mock_urlopen.return_value.read.return_value = json.dumps(resp).encode()

    with fake_gitlab_repo.dest.as_cwd():
        gitlab_pull_request.push(fake_gitlab_repo.settings, 'feature')

    # Should have pushed the branch to origin
    out = subprocess.check_output((
        'git', '-C', fake_gitlab_repo.src, 'branch',
    )).decode()
    assert out == '  feature\n* master\n'

    # Pull request should have been made with the commit data
    (req,), _ = mock_urlopen.call_args
    repo_slug = urllib.parse.quote(fake_gitlab_repo.src.strpath[1:], safe='')
    assert req.get_full_url() == (
        'https://gitlab.com/api/v4/projects'
        f'/{repo_slug}/merge_requests'
    )
    assert req.method == 'POST'
    data = json.loads(req.data)
    assert data['title'] == 'This is a commit message'
    assert data['description'] == 'Here is some more information!'
    assert data['target_branch'] == 'master'
    assert data['source_branch'] == 'feature'


@pytest.fixture
def fake_gitlab_repo_fork(tmpdir, fake_gitlab_repo):
    fork = tmpdir.join('repo:u2/slug')
    subprocess.check_call(('git', 'clone', fake_gitlab_repo.src, fork))

    settings = fake_gitlab_repo.settings._replace(fork=True)
    dct = dict(fake_gitlab_repo._asdict(), settings=settings, fork=fork)
    return auto_namedtuple(**dct)


def test_gitlab_pull_request_with_fork(mock_urlopen, fake_gitlab_repo_fork):
    resp_0 = [{'ssh_url_to_repo': fake_gitlab_repo_fork.fork.strpath}]
    resp_1 = {'web_url': 'foo'}
    mock_urlopen.return_value.read.side_effect = [
        json.dumps(resp).encode() for resp in (resp_0, resp_1)
    ]

    with fake_gitlab_repo_fork.dest.as_cwd():
        gitlab_pull_request.push(fake_gitlab_repo_fork.settings, 'feature')

    # Should have pushed the branch to the fork
    out = subprocess.check_output((
        'git', '-C', fake_gitlab_repo_fork.src, 'branch',
    )).decode()
    assert out == '* master\n'
    out = subprocess.check_output((
        'git', '-C', fake_gitlab_repo_fork.fork, 'branch',
    )).decode()
    assert out == '  feature\n* master\n'

    (req,), _ = mock_urlopen.call_args
    repo_slug = urllib.parse.quote(
        fake_gitlab_repo_fork.src.strpath[1:],
        safe='',
    )
    assert req.get_full_url() == (
        'https://gitlab.com/api/v4/projects'
        f'/{repo_slug}/merge_requests'
    )
    data = json.loads(req.data)
    assert data == {
        'source_branch': 'feature',
        'target_branch': 'master',
        'title': 'This is a commit message',
        'description': 'Here is some more information!',
        'remove_source_branch': True,
    }


def test_settings_repr():
    assert repr(gitlab_pull_request.Settings('secret')) == (
        'Settings(\n'
        '    api_key=...,\n'
        "    base_url='https://gitlab.com/api/v4',\n"
        '    fork=False,\n'
        ')'
    )
