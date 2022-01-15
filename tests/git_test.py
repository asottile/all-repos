from __future__ import annotations

import subprocess

from all_repos import git


def test_git_remote(tmpdir):
    r1 = tmpdir.join('1')
    r2 = tmpdir.join('2')
    subprocess.check_call(('git', 'init', r1))
    subprocess.check_call((
        'git', '-C', r1, 'commit', '--allow-empty', '-m', 'foo',
    ))
    subprocess.check_call(('git', 'clone', r1, r2))
    assert git.remote(r2) == r1
