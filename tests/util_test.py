from typing import NamedTuple

import pytest

from all_repos.push.github_pull_request import Settings
from all_repos.util import get_all
from all_repos.util import hide_api_key_repr
from all_repos.util import zsplit
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


@pytest.mark.parametrize(
    ('bs', 'expected'),
    (
        (b'', []),
        (b'\0', [b'']),
        (b'a\0b\0', [b'a', b'b']),
    ),
)
def test_zsplit(bs, expected):
    assert zsplit(bs) == expected


def test_hide_api_key_repr():
    assert hide_api_key_repr(Settings('secret', 'username')) == (
        'Settings(\n'
        '    api_key=...,\n'
        "    username='username',\n"
        '    fork=False,\n'
        "    base_url='https://api.github.com',\n"
        ')'
    )


def test_hide_api_key_different_key():
    class NT(NamedTuple):
        username: str
        password: str

    assert hide_api_key_repr(NT('user', 'pass'), key='password') == (
        'NT(\n'
        "    username='user',\n"
        '    password=...,\n'
        ')'
    )
