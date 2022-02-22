from __future__ import annotations

import json

import pytest

from all_repos.source.gitlab_org import list_repos
from all_repos.source.gitlab_org import Settings
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


def _resource_json(name):
    with open(f'testing/resources/gitlab/{name}.json') as f:
        return json.load(f)


@pytest.fixture
def repos_response(mock_urlopen):
    mock_urlopen.side_effect = urlopen_side_effect({
        'https://gitlab.com/api/v4/groups/ronny-test/'
        'projects?with_shared=False&include_subgroups=true': FakeResponse(
            json.dumps(_resource_json('org-listing')).encode(),
        ),
    })


def test_list_repos(repos_response):
    settings = Settings('key', 'ronny-test')
    ret = list_repos(settings)
    expected = {
        'ronny-test/test-repo': 'git@gitlab.com:ronny-test/test-repo.git',
    }
    assert ret == expected


def test_settings_repr():
    assert repr(Settings('key', 'sass')) == (
        'Settings(\n'
        '    api_key=...,\n'
        "    org='sass',\n"
        "    base_url='https://gitlab.com/api/v4',\n"
        '    archived=False,\n'
        ')'
    )
