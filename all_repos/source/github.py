import collections
from typing import Dict
from typing import List

import requests


Settings = collections.namedtuple(
    'Settings', ('api_key', 'username', 'collaborator', 'forks', 'private'),
)
Settings.__new__.__defaults__ = (False, False, False)


def _get_all(url: str, **kwargs) -> List[dict]:
    ret = []
    resp = requests.get(url, **kwargs)
    ret.extend(resp.json())
    while 'next' in resp.links:
        url = resp.links['next']['url']
        resp = requests.get(url, **kwargs)
        ret.extend(resp.json())
    return ret


def list_repos(settings: Settings) -> Dict[str, str]:
    repos = _get_all(
        'https://api.github.com/user/repos?per_page=100',
        auth=requests.auth.HTTPBasicAuth(settings.username, settings.api_key),
    )
    return {
        repo['full_name']: 'git@github.com:{}'.format(repo['full_name'])
        for repo in repos
        if (
            (settings.forks or not repo['fork']) and
            (settings.private or not repo['private']) and
            (settings.collaborator or repo['permissions']['admin'])
        )
    }


def better_repr(obj):
    if isinstance(obj, list):
        return [better_repr(o) for o in obj]
    elif isinstance(obj, dict):
        return {
            k: better_repr(v) for k, v in obj.items() if not k.endswith('url')
        }
    else:
        return obj
