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


def test_github_pull_request(mock_requests, fake_github_repo):
    with fake_github_repo.dest.as_cwd():
        github_pull_request.push(fake_github_repo.settings, 'feature')

    # Should have pushed the branch to origin
    out = subprocess.check_output((
        'git', '-C', fake_github_repo.src, 'branch',
    )).decode()
    assert out == '  feature\n* master\n'

    # Pull request should have been made with the commit data
    args, kwargs = mock_requests.post.call_args
    url, = args
    assert url == 'https://api.github.com/repos/user/slug/pulls'
    data = json.loads(kwargs['data'])
    assert data['title'] == 'This is a commit message'
    assert data['body'] == 'Here is some more information!'
    assert data['head'] == 'feature'
