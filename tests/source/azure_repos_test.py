from __future__ import annotations

import json

import pytest

from all_repos.source.azure_repos import list_repos
from all_repos.source.azure_repos import Settings
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


@pytest.fixture
def repositories_response(mock_urlopen):
    url = (
        'https://dev.azure.com/fake-organization/fake-project/'
        '_apis/git/repositories?api-version=6.0'
    )
    with open('testing/resources/azure_repos/list.json') as f:
        data = json.load(f)
    mock_urlopen.side_effect = urlopen_side_effect({
        url: FakeResponse(json.dumps(data).encode()),
    })


@pytest.mark.usefixtures('repositories_response')
def test_list_repos():
    settings = Settings(
        api_key='fake-token',
        organization='fake-organization',
        project='fake-project',
    )
    ret = list_repos(settings)
    ssh_url = (
        'git@ssh.dev.azure.com:v3/fake-organization/fake-project/fake-repo'
    )
    assert ret == {
        'fake-repo': ssh_url,
    }


def test_settings_repr():
    settings = Settings(
        api_key='fake-token',
        organization='fake-org',
        project='fake-project',
    )
    assert repr(settings) == (
        'Settings(\n'
        "    organization='fake-org',\n"
        "    project='fake-project',\n"
        "    base_url='https://dev.azure.com',\n"
        '    api_key=...,\n'
        '    api_key_env=None,\n'
        ')'
    )
