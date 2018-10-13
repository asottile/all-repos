import argparse
import re
from typing import List
from typing import Optional
from typing import Sequence
from typing import Set

from all_repos import autofix_lib
from all_repos.autofix.pre_commit_autoupdate import apply_fix as autoupdate
from all_repos.autofix.pre_commit_autoupdate import check_fix
from all_repos.autofix.pre_commit_autoupdate import tmp_pre_commit_home
from all_repos.config import Config
from all_repos.grep import repos_matching


def find_repos(config: Config) -> Set[str]:
    return repos_matching(
        config, ('autopep8-wrapper', '--', '.pre-commit-config.yaml'),
    )


REPO_LINE = re.compile('^-( +)repo:')
REV_LINE = re.compile('^( +)(rev|sha):')
AUTOPEP8_LINE = re.compile('^( +)-( +)id: autopep8-wrapper')
AUTOPEP8 = '''\
-{i1}repo: https://github.com/pre-commit/mirrors-autopep8
{i2}rev: v1.4
{i2}hooks:
{i3}-{i4}id: autopep8
'''


def apply_fix() -> None:
    with open('.pre-commit-config.yaml') as f:
        lines = list(f)

    i1 = i4 = ' ' * 3
    i2 = i3 = ' ' * 4

    new_lines: List[str] = []
    seen_autopep8 = False
    in_opts = False
    opt_lines: List[str] = []

    def add_mirrors_autopep8() -> None:
        new_lines.extend(AUTOPEP8.format(i1=i1, i2=i2, i3=i3, i4=i4))
        new_lines.extend(opt_lines)

    for line in lines:
        repo_match = REPO_LINE.match(line)
        rev_match = REV_LINE.match(line)
        autopep8_match = AUTOPEP8_LINE.match(line)

        if repo_match:
            i1 = repo_match.group(1)
        elif rev_match:
            i2 = rev_match.group(1)
        elif autopep8_match:
            i3, i4 = autopep8_match.groups()
            seen_autopep8 = in_opts = True
            continue

        if in_opts and not line.startswith(i3 + ' '):
            in_opts = False
        elif in_opts:
            opt_lines.append(line)
            continue

        if seen_autopep8 and repo_match:
            add_mirrors_autopep8()
            opt_lines = []
            seen_autopep8 = False

        new_lines.append(line)

    if seen_autopep8:
        add_mirrors_autopep8()

    with open('.pre-commit-config.yaml', 'w') as f:
        f.write(''.join(new_lines))

    autoupdate()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    autofix_lib.assert_importable('pre_commit', install='pre-commit')
    autofix_lib.require_version_gte('pre-commit', '1.7.0')

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Migrate from autopep8-wrapper to mirrors-autopep8',
        branch_name='pre-commit-autopep8-migrate',
    )

    with tmp_pre_commit_home():
        autofix_lib.fix(
            repos,
            apply_fix=apply_fix,
            check_fix=check_fix,
            config=config,
            commit=commit,
            autofix_settings=autofix_settings,
        )
    return 0


if __name__ == '__main__':
    exit(main())
