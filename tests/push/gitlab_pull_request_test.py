from __future__ import annotations

import json
import subprocess

import pytest

from all_repos.push import gitlab_pull_request
from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo


@pytest.fixture(
    params=[{}, {'draft': True}, {'assignee_ids': [1, 2]}],
    ids=['no-optional', 'draft', 'assignees'],
)
def fake_gitlab_repo(tmpdir, request):
    # hax: make the repo end with :repo/slug so it "looks" like a gitlab repo
    src = tmpdir.join('repo:user/slug')
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
    settings = gitlab_pull_request.Settings(api_key='fake', **request.param)
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
    assert out == '  feature\n* main\n'

    # Pull request should have been made with the commit data
    (req,), _ = mock_urlopen.call_args
    assert req.get_full_url() == (
        'https://gitlab.com/api/v4/projects'
        '/user%2Fslug/merge_requests'
    )
    assert req.method == 'POST'
    data = json.loads(req.data)

    expected_title = 'This is a commit message'
    if fake_gitlab_repo.settings.draft:
        expected_title = 'Draft: This is a commit message'

    assert data['title'] == expected_title
    assert data['description'] == 'Here is some more information!'
    assert data['target_branch'] == 'main'
    assert data['source_branch'] == 'feature'
    assert data['assignee_ids'] == fake_gitlab_repo.settings.assignee_ids


@pytest.fixture
def fake_gitlab_repo_fork(tmpdir, fake_gitlab_repo):
    fork = tmpdir.join('repo:u2/slug')
    subprocess.check_call(('git', 'clone', fake_gitlab_repo.src, fork))

    settings = fake_gitlab_repo.settings._replace(fork=True)
    dct = dict(fake_gitlab_repo._asdict(), settings=settings, fork=fork)
    return auto_namedtuple(**dct)


def test_gitlab_pull_request_with_fork(mock_urlopen, fake_gitlab_repo_fork):
    # this is a mishmash of both of the requests (satisfies both)
    resp = {'full_name': 'u2/slug', 'html_url': 'https://example/com'}
    mock_urlopen.return_value.read.return_value = json.dumps(resp).encode()

    with fake_gitlab_repo_fork.dest.as_cwd():
        with pytest.raises(NotImplementedError):
            gitlab_pull_request.push(fake_gitlab_repo_fork.settings, 'feature')

    # TODO: replicate github impl when implementing


def test_settings_repr():
    assert repr(gitlab_pull_request.Settings(api_key='secret')) == (
        'Settings(\n'
        "    base_url='https://gitlab.com/api/v4',\n"
        '    fork=False,\n'
        '    api_key=...,\n'
        '    api_key_env=None,\n'
        '    draft=False,\n'
        '    assignee_ids=None,\n'
        ')'
    )
