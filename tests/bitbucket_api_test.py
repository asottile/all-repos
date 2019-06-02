from all_repos.bitbucket_api import get_all
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


def test_get_all(mock_urlopen):
    mock_urlopen.side_effect = urlopen_side_effect({
        'https://example.com/api': FakeResponse(
            b'{"values":["page1_1", "page1_2"], "next":"https://example.com/api?page=2"}',  # noqa: E501,E261
        ),
        'https://example.com/api?page=2': FakeResponse(
            b'{"values":["page2_1", "page2_2"], "next":"https://example.com/api?page=3"}',  # noqa: E501,E261
        ),
        'https://example.com/api?page=3': FakeResponse(
            b'{"values":["page3_1", "page3_2"]}',
        ),
    })

    ret = get_all('https://example.com/api')

    expected = [
        'page1_1', 'page1_2',
        'page2_1', 'page2_2',
        'page3_1', 'page3_2',
    ]

    assert ret == expected
