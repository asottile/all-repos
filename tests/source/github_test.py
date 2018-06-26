import json

import pytest

from all_repos.source.github import list_repos
from all_repos.source.github import Settings
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


def _resource_json(repo_name: str) -> dict:
    with open(f'testing/resources/github/{repo_name}.json') as f:
        return json.load(f)


@pytest.fixture
def repos_response(mock_urlopen):
    repos = [
        # full permissions
        _resource_json('git-code-debt'),
        # A contributor repo
        _resource_json('libsass-python'),
        # A fork
        _resource_json('tox'),
        # A private repo
        _resource_json('eecs381-p4'),
    ]
    mock_urlopen.side_effect = urlopen_side_effect({
        'https://api.github.com/user/repos?per_page=100': FakeResponse(
            json.dumps(repos).encode(),
        ),
    })
    return repos


@pytest.mark.usefixtures('repos_response')
@pytest.mark.parametrize(
    ('settings', 'expected_repo_names'),
    (
        ({}, {'asottile/git-code-debt'}),
        (
            {'collaborator': True},
            {'asottile/git-code-debt', 'dahlia/libsass-python'},
        ),
        ({'forks': True}, {'asottile/git-code-debt', 'asottile/tox'}),
        ({'private': True}, {'asottile/git-code-debt', 'asottile/eecs381-p4'}),
    ),
)
def test_list_repos(settings, expected_repo_names):
    settings = Settings('key', 'user', **settings)
    ret = list_repos(settings)
    assert set(ret) == expected_repo_names
