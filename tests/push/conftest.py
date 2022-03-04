from __future__ import annotations

import subprocess
from typing import NamedTuple

import pytest

from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo


@pytest.fixture
def make_fake_bitbucket_repo(tmpdir):

    def _make_fake_bitbucket_repo(settings: NamedTuple) -> NamedTuple:
        # hax: make the repo end with proj/slug so it "looks" like
        # a bitbucket repo
        src = tmpdir.join('proj/slug')
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
        return auto_namedtuple(src=src, dest=dest, settings=settings)

    return _make_fake_bitbucket_repo
