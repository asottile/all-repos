from __future__ import annotations

from all_repos.bitbucket_server_api import get_all
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


def test_get_all(mock_urlopen):
    mock_urlopen.side_effect = urlopen_side_effect({
        'https://example.com/api?limit=2': FakeResponse(
            b'{'
            b'    "values":["page1_1", "page1_2"],'
            b'    "nextPageStart":3,'
            b'    "isLastPage":false'
            b'}',
        ),
        'https://example.com/api?limit=2&start=3': FakeResponse(
            b'{'
            b'    "values":["page2_1", "page2_2"],'
            b'    "nextPageStart":7,'
            b'    "isLastPage":false'
            b'}',
        ),
        'https://example.com/api?limit=2&start=7': FakeResponse(
            b'{"values":["page3_1", "page3_2"],"isLastPage":true}',
        ),
    })

    ret = get_all('https://example.com/api?limit=2')

    expected = [
        'page1_1', 'page1_2',
        'page2_1', 'page2_2',
        'page3_1', 'page3_2',
    ]

    assert ret == expected
