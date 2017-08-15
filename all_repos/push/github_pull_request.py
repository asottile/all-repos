import collections
import json
import subprocess

import requests

from all_repos import autofix_lib
from all_repos import git


Settings = collections.namedtuple('Settings', ('api_key', 'username'))


def push(settings: Settings, branch_name: str) -> None:
    autofix_lib.run('git', 'push', 'origin', f'HEAD:{branch_name}', '--quiet')

    title = subprocess.check_output(('git', 'log', '-1', '--format=%s'))
    body = subprocess.check_output(('git', 'log', '-1', '--format=%b'))

    data = json.dumps({
        'title': title.decode().strip(),
        'body': body.decode().strip(),
        'base': 'master',
        'head': branch_name,
    })

    repo_slug = git.remote('.').split(':')[-1]

    resp = requests.post(
        f'https://api.github.com/repos/{repo_slug}/pulls',
        data=data,
        auth=requests.auth.HTTPBasicAuth(settings.username, settings.api_key),
    )

    url = resp.json()['html_url']
    print(f'Pull request created at {url}')
