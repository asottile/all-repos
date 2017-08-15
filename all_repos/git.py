import subprocess


def remote(path: str) -> str:
    return subprocess.check_output((
        'git', '-C', path, 'config', 'remote.origin.url',
    )).decode().strip()
