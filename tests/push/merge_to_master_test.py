from __future__ import annotations

import subprocess

import pytest

import testing.git
from all_repos.push import merge_to_master
from testing.auto_namedtuple import auto_namedtuple


@pytest.fixture
def cloned(tmpdir):
    src = tmpdir.join('repo')
    testing.git.init_repo(src)

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
    ('settings', 'possible_commit_msgs'),
    [
        (
            merge_to_master.Settings(),
            testing.git.merge_msgs('feature'),
        ),
        (
            merge_to_master.Settings(fast_forward=False),
            testing.git.merge_msgs('feature'),
        ),
        (
            merge_to_master.Settings(fast_forward=True),
            {'This is a commit message\n\nHere is some more information!'},
        ),
    ],
)
def test_merge_to_master(cloned, settings, possible_commit_msgs):
    with cloned.dest.as_cwd():
        merge_to_master.push(settings, 'feature')
    # master is checked out
    branch_cmd = ('git', '-C', cloned.dest, 'branch')
    out = subprocess.check_output(branch_cmd).decode()
    assert out == '  feature\n* master\n'

    # check latest commit message
    msg_cmd = ('git', '-C', cloned.dest, 'log', '-1', '--pretty=%B')
    out = subprocess.check_output(msg_cmd).strip().decode()
    assert out in possible_commit_msgs
