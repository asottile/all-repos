from __future__ import annotations

import pytest

from all_repos import color


@pytest.mark.parametrize(
    ('use_color', 'expected'),
    (
        (True, '\033[41mtext\033[m'),
        (False, 'text'),
    ),
)
def test_fmt(use_color, expected):
    assert color.fmt('text', color.RED_H, use_color=use_color) == expected


@pytest.mark.parametrize(
    ('use_color', 'expected'),
    (
        (True, b'\033[41mbytes\033[m'),
        (False, b'bytes'),
    ),
)
def test_fmtb(use_color, expected):
    assert color.fmtb(b'bytes', color.RED_H, use_color=use_color) == expected
