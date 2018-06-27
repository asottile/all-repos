import json

import pytest

from all_repos.source.github_org import list_repos
from all_repos.source.github_org import Settings
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect
from tests.source.github_test import _resource_json


@pytest.fixture
def repos_response(mock_urlopen):
    mock_urlopen.side_effect = urlopen_side_effect({
        'https://api.github.com/orgs/sass/repos?per_page=100': FakeResponse(
            json.dumps([_resource_json('libsass-python')]).encode(),
        ),
    })


def test_list_repos(repos_response):
    settings = Settings('key', 'sass')
    ret = list_repos(settings)
    expected = {'sass/libsass-python': 'git@github.com:sass/libsass-python'}
    assert ret == expected
