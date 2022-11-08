from __future__ import annotations

import subprocess


def revparse(pth):
    rev = subprocess.check_output(('git', '-C', pth, 'rev-parse', 'HEAD'))
    return rev.decode().strip()


def init_repo(pth):
    subprocess.check_call(('git', 'init', pth))
    git = ('git', '-C', pth)
    subprocess.check_call((*git, 'branch', '-m', 'main'))
    subprocess.check_call((*git, 'commit', '--allow-empty', '-m', pth))
    subprocess.check_call((
        *git, 'config',
        'receive.denyCurrentBranch', 'updateInstead',
    ))
    return revparse(pth)


def commit(git):
    subprocess.check_call(('git', '-C', git, 'add', '.'))
    subprocess.check_call(('git', '-C', git, 'commit', '-mfoo'))


def write_file_commit(git, filename, contents):
    git.join(filename).write(contents)
    commit(git)


def merge_msgs(branch_name):
    return {
        f'Merge branch {branch_name!r}',  # git 2.25.1
        f'Merge branch {branch_name!r} into main',  # git 2.28.0
    }
