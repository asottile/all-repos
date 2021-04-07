import base64
import json
import subprocess
from typing import NamedTuple

from all_repos import autofix_lib
from all_repos import bitbucket_server_api
from all_repos import git
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    username: str
    app_password: str
    base_url: str

    @property
    def auth(self) -> str:
        value = f'{self.username}:{self.app_password}'
        return base64.b64encode(value.encode()).decode()

    def __repr__(self) -> str:
        return hide_api_key_repr(self, key='app_password')


def make_pull_request(
        settings: Settings,
        branch_name: str,
) -> bitbucket_server_api.Response:
    headers = {
        'Authorization': f'Basic {settings.auth}',
        'Content-Type': 'application/json',
    }

    remote = git.remote('.')
    remote_url = remote[:-len('.git')] if remote.endswith('.git') else remote
    *prefix, project, repo_slug = remote_url.split('/')
    head = branch_name

    autofix_lib.run('git', 'push', 'origin', f'HEAD:{branch_name}', '--quiet')

    title = subprocess.check_output(('git', 'log', '-1', '--format=%s'))
    body = subprocess.check_output(('git', 'log', '-1', '--format=%b'))

    data = json.dumps({
        'title': title.decode().strip(),
        'description': body.decode().strip(),
        'state': 'OPEN',
        'open': True,
        'closed': False,
        'fromRef': {
            'id': head,
            'repository': {
                'slug': repo_slug,
                'project': {
                    'key': project,
                },
            },
        },
        'toRef': {
            'id': autofix_lib.target_branch(),
            'repository': {
                'slug': repo_slug,
                'project': {
                    'key': project,
                },
            },
        },
        'locked': False,
        'reviewers': [],
    }).encode()

    end_point = f'projects/{project}/repos/{repo_slug}/pull-requests'
    return bitbucket_server_api.req(
        f'https://{settings.base_url}/rest/api/1.0/{end_point}',
        data=data, headers=headers, method='POST',
    )


def push(settings: Settings, branch_name: str) -> None:
    resp = make_pull_request(settings, branch_name)
    url = resp.links['self'][0]['href'] if resp.links else ''
    print(f'Pull request created at {url}')
