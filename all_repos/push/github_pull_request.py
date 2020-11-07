import json
import subprocess
from typing import NamedTuple

from all_repos import autofix_lib
from all_repos import git
from all_repos import github_api
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    api_key: str
    username: str
    fork: bool = False
    base_url: str = 'https://api.github.com'

    # TODO: https://github.com/python/mypy/issues/8543
    def __repr__(self) -> str:
        return hide_api_key_repr(self)


def make_pull_request(
        settings: Settings,
        branch_name: str,
) -> github_api.Response:
    headers = {'Authorization': f'token {settings.api_key}'}

    remote_url = git.remote('.')
    _, _, repo_slug = remote_url.rpartition(':')

    if settings.fork:
        resp = github_api.req(
            f'{settings.base_url}/repos/{repo_slug}/forks',
            headers=headers, method='POST',
        )
        new_slug = resp.json['full_name']
        new_remote = remote_url.replace(repo_slug, new_slug)
        autofix_lib.run('git', 'remote', 'add', 'fork', new_remote)
        remote = 'fork'
        head = f'{settings.username}:{branch_name}'
    else:
        remote = 'origin'
        head = branch_name

    autofix_lib.run('git', 'push', remote, f'HEAD:{branch_name}', '--quiet')

    title = subprocess.check_output(('git', 'log', '-1', '--format=%s'))
    body = subprocess.check_output(('git', 'log', '-1', '--format=%b'))

    data = json.dumps({
        'title': title.decode().strip(),
        'body': body.decode().strip(),
        'base': autofix_lib.target_branch(),
        'head': head,
    }).encode()

    return github_api.req(
        f'{settings.base_url}/repos/{repo_slug}/pulls',
        data=data, headers=headers, method='POST',
    )


def push(settings: Settings, branch_name: str) -> None:
    resp = make_pull_request(settings, branch_name)
    url = resp.json['html_url']
    print(f'Pull request created at {url}')
