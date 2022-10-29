from __future__ import annotations

import argparse
import contextlib
import functools
import json
import subprocess
from typing import Sequence

from all_repos import autofix_lib
from all_repos import git
from all_repos import sed
from all_repos.config import Config
from all_repos.github_api import req

# LOOK AWAY!
autofix_lib.target_branch = lambda: 'main'
# OK FINE AFTER HERE!


def get_github_repo_slug() -> str:
    remote_url = git.remote('.')
    _, _, repo_slug = remote_url.rpartition(':')
    return repo_slug


def find_repos(config: Config) -> set[str]:
    raise NotImplementedError('specify repos manually!')


def apply_fix(*, dry_run: bool) -> None:
    with open('/home/asottile/.github-auth.json') as f:
        contents = json.load(f)

    headers = {'Authorization': f'token {contents["token"]}'}

    if not dry_run:
        repo = get_github_repo_slug()
        req(
            f'https://api.github.com/repos/{repo}/branches/master/rename',
            method='POST',
            headers=headers,
            data=json.dumps({'new_name': 'main'}).encode(),
        )

    # call all-repos-sed
    with contextlib.suppress(subprocess.CalledProcessError):
        sed.apply_fix(
            ls_files_cmd=(
                'git', 'ls-files', '-z', '--',
                'README.md',
                'CONTRIBUTING.md',
                'azure-pipelines.yml',
                '.github/workflows/*',
            ),
            sed_cmd=('sed', '-i', r's/\bmaster\b/main/g'),
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Update default branch to main',
        branch_name='master-to-main',
    )

    autofix_lib.fix(
        repos,
        apply_fix=functools.partial(
            apply_fix,
            dry_run=autofix_settings.dry_run,
        ),
        config=config,
        commit=commit,
        autofix_settings=autofix_settings,
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
