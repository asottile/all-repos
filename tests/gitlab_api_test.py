from __future__ import annotations

import json

from all_repos.gitlab_api import get_all
from all_repos.gitlab_api import get_group_id
from all_repos.gitlab_api import get_project_id
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


def test_get_all(mock_urlopen):
    mock_urlopen.side_effect = urlopen_side_effect({
        'https://example.com/api': FakeResponse(
            b'["page1_1", "page1_2"]',
            next_link='https://example.com/api?page=2',
        ),
        'https://example.com/api?page=2': FakeResponse(
            b'["page2_1", "page2_2"]',
            next_link='https://example.com/api?page=3',
        ),
        'https://example.com/api?page=3': FakeResponse(
            b'["page3_1"]',
        ),
    })

    ret = get_all('https://example.com/api')
    assert ret == ['page1_1', 'page1_2', 'page2_1', 'page2_2', 'page3_1']


def test_get_group_id(mock_urlopen):
    mock_urlopen.side_effect = urlopen_side_effect({
        'https://gitlab.com/api/v4/groups/some-group': FakeResponse(
            json.dumps({'id': 999}).encode(),
        ),
    })

    class S:
        base_url = 'https://gitlab.com/api/v4'
        org = 'some-group'
        api_key = 'k'
        api_key_env = None

    assert get_group_id(S) == '999'


def test_get_project_id(mock_urlopen):
    mock_urlopen.side_effect = urlopen_side_effect({
        'https://gitlab.com/api/v4/projects/my%2Frepo': FakeResponse(
            json.dumps({'id': 999}).encode(),
        ),
    })

    class S:
        base_url = 'https://gitlab.com/api/v4'
        api_key = 'k'
        api_key_env = None

    # should return the quoted slug when resolution fails
    assert get_project_id(S, 'my/repo') == '999'
