import collections
import json
import urllib.request
from typing import Dict
from typing import List


Settings = collections.namedtuple(
    'Settings', ('api_key', 'username', 'collaborator', 'forks', 'private'),
)
Settings.__new__.__defaults__ = (False, False, False)


def _parse_link_header(lnk):
    if lnk is None:
        return {}

    ret = {}
    parts = lnk.split(',')
    for part in parts:
        link, _, rel = part.partition(';')
        link, rel = link.strip(), rel.strip()
        assert link.startswith('<') and link.endswith('>'), link
        assert rel.startswith('rel="') and rel.endswith('"'), rel
        link, rel = link[1:-1], rel[len('rel="'):-1]
        ret[rel] = link
    return ret


def _req(*args, **kwargs):
    resp = urllib.request.urlopen(urllib.request.Request(*args, **kwargs))
    return json.loads(resp.read()), _parse_link_header(resp.headers['link'])


def _get_all(url: str, **kwargs) -> List[dict]:
    ret = []
    resp, links = _req(url, **kwargs)
    ret.extend(resp)
    while 'next' in links:
        resp, links = _req(links['next'], **kwargs)
        ret.extend(resp)
    return ret


def list_repos(settings: Settings) -> Dict[str, str]:
    repos = _get_all(
        'https://api.github.com/user/repos?per_page=100',
        headers={'Authorization': f'token {settings.api_key}'},
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
