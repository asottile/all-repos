import argparse
import functools
import urllib.request
from typing import Optional
from typing import Sequence
from typing import Set

from all_repos import autofix_lib
from all_repos import github_api
from all_repos.config import Config
from all_repos.push.github_pull_request import get_github_repo_slug

BADGE = '[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/{repo_slug}/master.svg)](https://results.pre-commit.ci/latest/github/{repo_slug}/master)\n'  # noqa: E501


def find_repos(config: Config) -> Set[str]:
    return set()  # require repos to be specified on the commandline


def add_repo_to_install(config: Config, install: int, repo: str) -> None:
    headers = {'Authorization': f'token {config.source_settings.api_key}'}
    repo_resp = github_api.req(
        f'https://api.github.com/repos/{repo}',
        headers=headers,
    )
    repo_id = repo_resp.json['id']

    # can't use the `github_api` helper as this returns 204 No Content
    request = urllib.request.Request(
        f'https://api.github.com/user/installations/{install}/repositories/{repo_id}',  # noqa: E501
        method='PUT',
        headers=headers,
    )
    urllib.request.urlopen(request)


def apply_fix(*, config: Config, dry_run: bool, install_id: int) -> None:
    repo_slug = get_github_repo_slug()
    if dry_run:
        print(f'would have added {repo_slug} to install {install_id}')
    else:
        add_repo_to_install(config, install_id, repo_slug)

    with open('README.md') as f:
        lines = list(f)

    i = 0
    while lines[i].startswith('['):
        i += 1
    if i == 0:
        lines.insert(i, '\n')
    lines.insert(i, BADGE.format(repo_slug=repo_slug))
    with open('README.md', 'w') as f:
        f.writelines(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--install-id', type=int, required=True,
        help=(
            'The pre-commit.ci install id to add the repository to.  '
            'One can retrieve the install id from the user / organization '
            'page on pre-commit.ci.  '
            'For example, this install id is 12617958: '
            'https://results.pre-commit.ci/install/github/12617958'
        ),
    )
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Use pre-commit.ci',
        branch_name='pre-commit-ci',
    )

    autofix_lib.fix(
        repos,
        apply_fix=functools.partial(
            apply_fix,
            config=config,
            dry_run=args.dry_run,
            install_id=args.install_id,
        ),
        config=config,
        commit=commit,
        autofix_settings=autofix_settings,
    )
    return 0


if __name__ == '__main__':
    exit(main())
