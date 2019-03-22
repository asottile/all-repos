import re
from typing import List

from all_repos.autofix.pre_commit_autoupdate import apply_fix as autoupdate

REPO_LINE = re.compile('^-( +)repo:')
REV_LINE = re.compile('^( +)(rev|sha):')
NEW_REPO = '''\
-{i1}repo: {repo}
{i2}rev: {rev}
{i2}hooks:
{i3}-{i4}id: {hook}
'''


def apply_fix_fn(*, prev_hook: str, repo: str, rev: str, hook: str) -> None:
    hook_line = re.compile(f'^( +)-( +)id: {prev_hook}')

    with open('.pre-commit-config.yaml') as f:
        lines = list(f)

    i1 = i4 = ' ' * 3
    i2 = i3 = ' ' * 4

    new_lines: List[str] = []
    seen_hook = False
    in_opts = False
    opt_lines: List[str] = []

    def add_new_repo() -> None:
        new_lines.extend(
            NEW_REPO.format(
                i1=i1, i2=i2, i3=i3, i4=i4, repo=repo, rev=rev, hook=hook,
            ),
        )
        new_lines.extend(opt_lines)

    for line in lines:
        repo_match = REPO_LINE.match(line)
        rev_match = REV_LINE.match(line)
        hook_match = hook_line.match(line)

        if repo_match:
            i1 = repo_match.group(1)
        elif rev_match:
            i2 = rev_match.group(1)
        elif hook_match:
            i3, i4 = hook_match.groups()
            seen_hook = in_opts = True
            continue

        if in_opts and not line.startswith(i3 + ' '):
            in_opts = False
        elif in_opts:
            opt_lines.append(line)
            continue

        if seen_hook and repo_match:
            add_new_repo()
            opt_lines = []
            seen_hook = False

        new_lines.append(line)

    if seen_hook:
        add_new_repo()

    with open('.pre-commit-config.yaml', 'w') as f:
        f.write(''.join(new_lines))

    autoupdate()
