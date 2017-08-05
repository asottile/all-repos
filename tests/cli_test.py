import multiprocessing

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
