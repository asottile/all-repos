from __future__ import annotations

import json
import os
from unittest import mock

import pytest

from all_repos.source.github import list_repos
from all_repos.source.github import Settings
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


def _resource_json(repo_name):
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
        # An archived repo
        _resource_json('poi-map'),
        # A repo owned by user
        _resource_json('user-empty'),
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
        ({}, {'asottile/git-code-debt', 'user/new'}),
        (
            {'collaborator': True},
            {'asottile/git-code-debt', 'sass/libsass-python', 'user/new'},
        ),
        (
            {'forks': True},
            {'asottile/git-code-debt', 'asottile/tox', 'user/new'},
        ),
        (
            {'private': True},
            {'asottile/git-code-debt', 'asottile/eecs381-p4', 'user/new'},
        ),
        (
            {'archived': True},
            {'asottile/git-code-debt', 'asottile-archive/poi-map', 'user/new'},
        ),
        ({'owner': True}, {'user/new'}),
    ),
)
def test_list_repos(settings, expected_repo_names):
    settings = Settings(api_key='key', username='user', **settings)
    ret = list_repos(settings)
    assert set(ret) == expected_repo_names


def test_settings_repr():
    settings = Settings(api_key='api_key', username='user')

    assert repr(settings) == (
        'Settings(\n'
        "    username='user',\n"
        '    collaborator=False,\n'
        '    owner=False,\n'
        '    forks=False,\n'
        '    private=False,\n'
        '    archived=False,\n'
        "    base_url='https://api.github.com',\n"
        '    api_key=...,\n'
        '    api_key_env=None,\n'
        ')'
    )


def test_list_repos_api_key_via_env_var(monkeypatch, mock_urlopen):
    settings = Settings(api_key_env='MAGIC', username='U')

    url = 'https://api.github.com/user/repos?per_page=100'
    mock_urlopen.side_effect = urlopen_side_effect({url: FakeResponse(b'[]')})

    with mock.patch.dict(os.environ, {'MAGIC': 'M'}):
        ret = list_repos(settings)
    assert not ret
    mock_urlopen.assert_called_once()
    assert mock_urlopen.call_args[0][0].headers == {'Authorization': 'token M'}


def test_list_repos_api_key_via_env_var_not_set(monkeypatch):
    settings = Settings(api_key_env='MAGIC', username='U')

    with pytest.raises(ValueError) as excinfo:
        with mock.patch.dict(os.environ, clear=True):
            list_repos(settings)
    msg, = excinfo.value.args
    assert msg == 'api_key_env (MAGIC) not set'


def test_list_repos_api_key_via_env_var_and_env_not_set():
    settings = Settings(username='U')
    with pytest.raises(ValueError) as excinfo:
        list_repos(settings)
    msg, = excinfo.value.args
    assert msg == 'expected exactly one of: api_key, api_key_env'
