from __future__ import annotations

import base64
import json
import subprocess
import urllib.request
from typing import Any
from typing import NamedTuple

from all_repos import autofix_lib
from all_repos import git
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    api_key: str
    organization: str
    project: str
    base_url: str = 'https://dev.azure.com'

    def __repr__(self) -> str:
        return hide_api_key_repr(self)

    @property
    def auth(self) -> str:
        value = f':{self.api_key}'
        return base64.b64encode(value.encode()).decode()


def make_pull_request(
        settings: Settings,
        branch_name: str,
) -> Any:
    headers = {
        'Authorization': f'Basic {settings.auth}',
        'Content-Type': 'application/json',
    }

    remote_url = git.remote('.')
    *prefix, repo_slug = remote_url.split('/')
    remote = 'origin'
    head = branch_name

    autofix_lib.run('git', 'push', remote, f'HEAD:{branch_name}', '--quiet')

    title = subprocess.check_output(('git', 'log', '-1', '--format=%s'))
    body = subprocess.check_output(('git', 'log', '-1', '--format=%b'))

    data = json.dumps({
        'title': title.decode().strip(),
        'description': body.decode().strip(),
        'sourceRefName': f'refs/heads/{head}',
        'targetRefName': f'refs/heads/{autofix_lib.target_branch()}',
    }).encode()

    pull_request_url = (
        f'{settings.base_url}/{settings.organization}/{settings.project}/'
        f'_apis/git/repositories/{repo_slug}/pullrequests?api-version=6.0'
    )

    resp = urllib.request.urlopen(
        urllib.request.Request(
            pull_request_url, data=data, headers=headers, method='POST',
        ),
    )
    return json.load(resp)


def push(settings: Settings, branch_name: str) -> None:
    obj = make_pull_request(settings, branch_name)
    web_url = obj['repository']['webUrl']
    pr_id = obj['pullRequestId']
    url = f'{web_url}/pullrequest/{pr_id}'
    print(f'Pull request created at {url}')
