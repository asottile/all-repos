import collections

from all_repos import autofix_lib


Settings = collections.namedtuple('Settings', ())


def push(settings: Settings, branch_name: str) -> None:
    autofix_lib.run('git', 'checkout', autofix_lib.target_branch(), '--quiet')
    autofix_lib.run('git', 'pull', '--quiet')
    autofix_lib.run(
        'git', 'merge', '--no-edit', '--no-ff', branch_name, '--quiet',
    )
    autofix_lib.run('git', 'push', 'origin', 'HEAD', '--quiet')
