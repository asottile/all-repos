from __future__ import annotations

import multiprocessing
import sys
from unittest import mock

import pytest

from all_repos import cli


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        ('0', multiprocessing.cpu_count()),
        ('-1', multiprocessing.cpu_count()),
        ('1', 1),
        ('2', 2),
    ),
)
def test_jobs_type(s, expected):
    assert cli.jobs_type(s) == expected


@pytest.mark.parametrize(
    ('setting', 'tty', 'expected'),
    (
        ('auto', True, True),
        ('auto', False, False),
        ('always', True, True),
        ('always', False, True),
        ('never', True, False),
        ('never', False, False),
    ),
)
def test_color_setting(setting, tty, expected):
    with mock.patch.object(sys.stdout, 'isatty', return_value=tty):
        assert cli.use_color(setting) is expected


def test_color_setting_invalid():
    with pytest.raises(ValueError):
        cli.use_color('wat')
