from __future__ import annotations

import json

import pytest

from all_repos.source.bitbucket_server import list_repos
from all_repos.source.bitbucket_server import Settings
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


def _resource_json():
    with open('testing/resources/bitbucket/list.json') as f:
        return json.load(f)


@pytest.fixture
def repos_response(mock_urlopen):
    url = 'https://bitbucket.domain.com/' \
        'rest/api/1.0/repos?limit=100&permission=REPO_READ'
    mock_urlopen.side_effect = urlopen_side_effect({
        url: FakeResponse(json.dumps(_resource_json()).encode()),
    })


@pytest.fixture
def repos_project_response(mock_urlopen):
    url = 'https://bitbucket.domain.com/' \
        'rest/api/1.0/projects/PRJ/repos?limit=100&permission=REPO_READ'
    mock_urlopen.side_effect = urlopen_side_effect({
        url: FakeResponse(json.dumps(_resource_json()).encode()),
    })


@pytest.mark.usefixtures('repos_response')
def test_list_repos():
    settings = Settings(
        'cool_user', 'app_password', 'bitbucket.domain.com',
    )
    ret = list_repos(settings)
    assert ret == {
        'fake_proj/fake_repo': 'ssh://git@bitbucket.domain.com/'
        'fake_proj/fake_repo.git',
    }


@pytest.mark.usefixtures('repos_project_response')
def test_list_repos_from_project():
    settings = Settings(
        'cool_user', 'app_password', 'bitbucket.domain.com', 'PRJ',
    )
    ret = list_repos(settings)
    assert ret == {
        'fake_proj/fake_repo': 'ssh://git@bitbucket.domain.com/'
        'fake_proj/fake_repo.git',
    }


def test_settings_repr():
    settings = Settings('cool_user', 'app_password', 'bitbucket.domain.com')
    assert repr(settings) == (
        'Settings(\n'
        "    username='cool_user',\n"
        '    app_password=...,\n'
        "    base_url='bitbucket.domain.com',\n"
        '    project=None,\n'
        ')'
    )
