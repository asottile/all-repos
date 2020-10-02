import json
import urllib.request
from typing import Any
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import TypeVar


class Response(NamedTuple):
    json: Any
    links: Dict[str, str]


def _parse_link(lnk: Optional[str]) -> Dict[str, str]:
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


def req(url: str, **kwargs: Any) -> Response:
    resp = urllib.request.urlopen(urllib.request.Request(url, **kwargs))
    return Response(json.load(resp), _parse_link(resp.headers['link']))


def get_all(url: str, **kwargs: Any) -> List[Dict[str, Any]]:
    ret: List[Dict[str, Any]] = []
    resp = req(url, **kwargs)
    ret.extend(resp.json)
    while 'next' in resp.links:
        resp = req(resp.links['next'], **kwargs)
        ret.extend(resp.json)
    return ret


def _strip_trailing_dot_git(ssh_url: str) -> str:
    if ssh_url.endswith('.git'):
        return ssh_url[:-1 * len('.git')]
    else:
        return ssh_url


def filter_repos(
        repos: List[Dict[str, Any]], *,
        forks: bool, private: bool, collaborator: bool, archived: bool,
) -> Dict[str, str]:
    return {
        repo['full_name']: _strip_trailing_dot_git(repo['ssh_url'])
        for repo in repos
        if (
            (forks or not repo['fork']) and
            (private or not repo['private']) and
            (collaborator or repo['permissions']['admin']) and
            (archived or not repo['archived'])
        )
    }


T = TypeVar('T', List[Any], Dict[str, Any], Any)


def better_repr(obj: T) -> T:
    if isinstance(obj, list):
        return [better_repr(o) for o in obj]
    elif isinstance(obj, dict):
        return {
            k: better_repr(v) for k, v in obj.items() if not k.endswith('url')
        }
    else:
        return obj
