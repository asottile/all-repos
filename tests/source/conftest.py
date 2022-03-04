from __future__ import annotations

import json

import pytest

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
