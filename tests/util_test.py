from __future__ import annotations

from typing import NamedTuple

import pytest

from all_repos.push.github_pull_request import Settings
from all_repos.util import hide_api_key_repr
from all_repos.util import zsplit


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
    settings = Settings(api_key='secret', username='username')
    assert hide_api_key_repr(settings) == (
        'Settings(\n'

        "    username='username',\n"
        '    fork=False,\n'
        "    base_url='https://api.github.com',\n"
        '    api_key=...,\n'
        '    api_key_env=None,\n'
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
