import json
import subprocess
import urllib.parse
from typing import NamedTuple

from all_repos import autofix_lib
from all_repos import git
from all_repos import gitlab_api
from all_repos.github_api import _strip_trailing_dot_git
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    api_key: str
    base_url: str = 'https://gitlab.com/api/v4'
    fork: bool = False

    def __repr__(self) -> str:
        return hide_api_key_repr(self)


# https://gitlab.com/gitlab-org/gitlab-ce/issues/64320


def push(settings: Settings, branch_name: str) -> None:
    headers = {
        'Private-Token': settings.api_key,
        'Content-Type': 'application/json',
    }

    remote_url = git.remote('.')
    _, _, repo_slug = remote_url.rpartition(':')
    repo_slug = _strip_trailing_dot_git(repo_slug)
    repo_slug = urllib.parse.quote(repo_slug, safe='')
    if settings.fork:
        raise NotImplementedError('fork support  not yet implemented')
    else:
        remote = 'origin'
        head = branch_name

    autofix_lib.run('git', 'push', remote, f'HEAD:{head}', '--quiet')

    title = subprocess.check_output(('git', 'log', '-1', '--format=%s'))
    body = subprocess.check_output(('git', 'log', '-1', '--format=%b'))

    data = json.dumps({
        'source_branch': head,
        'target_branch': autofix_lib.target_branch(),
        'title': title.decode().strip(),
        'description': body.decode().strip(),
    }).encode()

    resp = gitlab_api.req(
        f'{settings.base_url}/projects/{repo_slug}/merge_requests',
        data=data, headers=headers, method='POST',
    )
    url = resp.json['web_url']
    print(f'Pull request created at {url}')
