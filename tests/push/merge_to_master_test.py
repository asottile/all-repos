import subprocess

import pytest

from all_repos.push import merge_to_master
from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo


@pytest.fixture
def cloned(tmpdir):
    src = tmpdir.join('repo')
    init_repo(src)

    dest = tmpdir.join('dest')
    subprocess.check_call(('git', 'clone', src, dest))
    subprocess.check_call((
        'git', '-C', dest, 'checkout', 'origin/master', '-b', 'feature',
    ))
    subprocess.check_call((
        'git', '-C', dest, 'commit', '--allow-empty',
        '-m', 'This is a commit message\n\nHere is some more information!',
    ))
    return auto_namedtuple(src=src, dest=dest)


@pytest.mark.parametrize(
    ("settings", "expected_commit_message"),
    [
        (
            merge_to_master.Settings(),
            "Merge branch 'feature'",
        ),
        (
            merge_to_master.Settings(fast_forward=False),
            "Merge branch 'feature'",
        ),
        (
            merge_to_master.Settings(fast_forward=True),
            'This is a commit message\n\nHere is some more information!',
        ),
    ],
)
def test_merge_to_master(cloned, settings, expected_commit_message):
    with cloned.dest.as_cwd():
        merge_to_master.push(settings, 'feature')
    # master is checked out
    out = subprocess.check_output((
        'git', '-C', cloned.dest, 'branch',
    )).decode()
    assert out == '  feature\n* master\n'

    # check latest commit message
    out = subprocess.check_output((
        'git', '-C', cloned.dest, 'log', '-1', '--pretty=%B',
    )).decode().strip()
    assert out == expected_commit_message
