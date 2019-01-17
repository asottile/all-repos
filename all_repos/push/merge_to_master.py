from typing import NamedTuple

from all_repos import autofix_lib


class Settings(NamedTuple):
    fast_forward: bool = False


def push(settings: Settings, branch_name: str) -> None:
    autofix_lib.run('git', 'checkout', autofix_lib.target_branch(), '--quiet')
    autofix_lib.run('git', 'pull', '--quiet')
    ff_flag = '--ff-only' if settings.fast_forward else '--no-ff'
    autofix_lib.run(
        'git', 'merge', '--no-edit', ff_flag, branch_name, '--quiet',
    )
    autofix_lib.run('git', 'push', 'origin', 'HEAD', '--quiet')
