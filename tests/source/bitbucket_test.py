import json

import pytest

from all_repos.source.bitbucket import list_repos
from all_repos.source.bitbucket import Settings
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


def _resource_json():
    with open(f'testing/resources/bitbucket/fake.json') as f:
        return json.load(f)


@pytest.fixture
def repos_response(mock_urlopen):
    mock_urlopen.side_effect = urlopen_side_effect({
        'https://api.bitbucket.org/2.0/repositories?pagelen=100&role=member': FakeResponse(  # noqa: E501
            json.dumps(_resource_json()).encode(),
        ),
    })


@pytest.mark.usefixtures('repos_response')
def test_list_repos():
    settings = Settings('cool_user', 'app_password')
    ret = list_repos(settings)
    expected = {'fake_org/fake_repo': 'git@bitbucket.org:fake_org/fake_repo.git'}  # noqa: E501
    assert ret == expected
