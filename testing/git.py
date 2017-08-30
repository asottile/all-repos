import subprocess


def revparse(pth):
    rev = subprocess.check_output(('git', '-C', pth, 'rev-parse', 'HEAD'))
    return rev.decode().strip()


def init_repo(pth):
    subprocess.check_call(('git', 'init', pth))
    subprocess.check_call((
        'git', '-C', pth, 'commit', '--allow-empty', '-m', pth,
    ))
    subprocess.check_call((
        'git', '-C', pth, 'config',
        'receive.denyCurrentBranch', 'updateInstead',
    ))
    return revparse(pth)
