from __future__ import annotations

import pytest

from all_repos.source.bitbucket_server_bearer_auth import list_repos
from all_repos.source.bitbucket_server_bearer_auth import Settings


@pytest.mark.usefixtures('repos_response')
def test_list_repos():
    settings = Settings(
        'token', 'bitbucket.domain.com',
    )
    ret = list_repos(settings)
    assert ret == {
        'fake_proj/fake_repo': 'ssh://git@bitbucket.domain.com/'
        'fake_proj/fake_repo.git',
    }


@pytest.mark.usefixtures('repos_project_response')
def test_list_repos_from_project():
    settings = Settings(
        'token', 'bitbucket.domain.com', 'PRJ',
    )
    ret = list_repos(settings)
    assert ret == {
        'fake_proj/fake_repo': 'ssh://git@bitbucket.domain.com/'
        'fake_proj/fake_repo.git',
    }


def test_settings_repr():
    settings = Settings('token', 'bitbucket.domain.com')
    assert repr(settings) == (
        'Settings(\n'
        '    token=...,\n'
        "    base_url='bitbucket.domain.com',\n"
        '    project=None,\n'
        ')'
    )
