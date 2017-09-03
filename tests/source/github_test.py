import json
import os.path

import pytest
import requests

from all_repos.source.github import _get_all
from all_repos.source.github import better_repr
from all_repos.source.github import list_repos
from all_repos.source.github import Settings


@pytest.mark.parametrize(
    ('val', 'expected'),
    (
        ({}, {}),
        ({'foo': 'bar'}, {'foo': 'bar'}),
        ({'foo': 'bar', 'image_url': 'https://...'}, {'foo': 'bar'}),
        (
            {
                'foo': 'bar',
                'nested': {
                    'image_url': 'https://...',
                    'baz': 'womp',
                },
            },
            {'foo': 'bar', 'nested': {'baz': 'womp'}},
        ),
        (
            [{
                'foo': 'bar',
                'image_url': 'https://...',
            }],
            [{'foo': 'bar'}],
        ),
    ),
)
def test_better_repr(val, expected):
    assert better_repr(val) == expected


def _mock_get(url_mapping):
    def get(url, **kwargs):
        return url_mapping[url]
    return get


def _fake_response(body, *, next_link=None):
    resp = requests.Response()
    resp._content = body
    if next_link is not None:
        resp.headers['Link'] = f'<{next_link}>; rel="next"'
    return resp


def test_get_all(mock_requests):
    mock_requests.get.side_effect = _mock_get({
        'https://example.com/api': _fake_response(
            b'["page1_1", "page1_2"]',
            next_link='https://example.com/api?page=2',
        ),
        'https://example.com/api?page=2': _fake_response(
            b'["page2_1", "page2_2"]',
            next_link='https://example.com/api?page=3',
        ),
        'https://example.com/api?page=3': _fake_response(
            b'["page3_1"]',
        ),
    })

    ret = _get_all('https://example.com/api')
    assert ret == ['page1_1', 'page1_2', 'page2_1', 'page2_2', 'page3_1']


def _resource_json(repo_name: str) -> dict:
    path = os.path.join('testing/resources/github', f'{repo_name}.json')
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def repos_response(mock_requests):
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
    mock_requests.get.side_effect = _mock_get({
        'https://api.github.com/user/repos?per_page=100': _fake_response(
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
