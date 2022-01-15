from __future__ import annotations

import pytest

from all_repos.github_api import _strip_trailing_dot_git
from all_repos.github_api import better_repr
from all_repos.github_api import get_all
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


@pytest.mark.parametrize(
    ('val', 'expected'),
    (
        ({}, {}),
        ({'foo': 'bar'}, {'foo': 'bar'}),
        ({'foo': 'bar', 'image_url': 'https://...'}, {'foo': 'bar'}),
        (
            {
                'foo': 'bar',
                'nested': {
                    'image_url': 'https://...',
                    'baz': 'womp',
                },
            },
            {'foo': 'bar', 'nested': {'baz': 'womp'}},
        ),
        (
            [{
                'foo': 'bar',
                'image_url': 'https://...',
            }],
            [{'foo': 'bar'}],
        ),
    ),
)
def test_better_repr(val, expected):
    assert better_repr(val) == expected


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
    ('val', 'expected'),
    (
        ('', ''),
        (
            'git@github.com:sass/libsass-python',
            'git@github.com:sass/libsass-python',
        ),
        (
            'git@github.com:sass/libsass-python.git',
            'git@github.com:sass/libsass-python',
        ),
        (
            'git@github.com:.git/example',
            'git@github.com:.git/example',
        ),
    ),
)
def test_strip_trailing_dot_git(val, expected):
    assert _strip_trailing_dot_git(val) == expected
