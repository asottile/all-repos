from __future__ import annotations

import json
import subprocess

import pytest

from all_repos.push import github_pull_request
from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo


@pytest.fixture
def fake_github_repo(tmpdir):
    # hax: make the repo end with :repo/slug so it "looks" like a github repo
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
    settings = github_pull_request.Settings(api_key='fake', username='user')
    return auto_namedtuple(src=src, dest=dest, settings=settings)


def test_github_pull_request(mock_urlopen, fake_github_repo):
    resp = {'html_url': 'https://example/com'}
    mock_urlopen.return_value.read.return_value = json.dumps(resp).encode()

    with fake_github_repo.dest.as_cwd():
        github_pull_request.push(fake_github_repo.settings, 'feature')

    # Should have pushed the branch to origin
    out = subprocess.check_output((
        'git', '-C', fake_github_repo.src, 'branch',
    )).decode()
    assert out == '  feature\n* master\n'

    # Pull request should have been made with the commit data
    (req,), _ = mock_urlopen.call_args
    assert req.get_full_url() == 'https://api.github.com/repos/user/slug/pulls'
    assert req.method == 'POST'
    data = json.loads(req.data)
    assert data['title'] == 'This is a commit message'
    assert data['body'] == 'Here is some more information!'
    assert data['head'] == 'feature'


@pytest.fixture
def fake_github_repo_fork(tmpdir, fake_github_repo):
    fork = tmpdir.join('repo:u2/slug')
    subprocess.check_call(('git', 'clone', fake_github_repo.src, fork))

    settings = fake_github_repo.settings._replace(fork=True, username='u2')
    dct = dict(fake_github_repo._asdict(), settings=settings, fork=fork)
    return auto_namedtuple(**dct)


def test_github_pull_request_with_fork(mock_urlopen, fake_github_repo_fork):
    # this is a mishmash of both of the requests (satisfies both)
    resp = {'full_name': 'u2/slug', 'html_url': 'https://example/com'}
    mock_urlopen.return_value.read.return_value = json.dumps(resp).encode()

    with fake_github_repo_fork.dest.as_cwd():
        github_pull_request.push(fake_github_repo_fork.settings, 'feature')

    # Should have pushed the branch to the fork
    out = subprocess.check_output((
        'git', '-C', fake_github_repo_fork.src, 'branch',
    )).decode()
    assert out == '* master\n'
    out = subprocess.check_output((
        'git', '-C', fake_github_repo_fork.fork, 'branch',
    )).decode()
    assert out == '  feature\n* master\n'

    (req,), _ = mock_urlopen.call_args
    assert req.get_full_url() == 'https://api.github.com/repos/user/slug/pulls'
    data = json.loads(req.data)
    assert data['head'] == 'u2:feature'


def test_settings_repr():
    assert repr(github_pull_request.Settings('secret', 'username')) == (
        'Settings(\n'
        '    api_key=...,\n'
        "    username='username',\n"
        '    fork=False,\n'
        "    base_url='https://api.github.com',\n"
        ')'
    )
