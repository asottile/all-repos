import json
import urllib.request
from typing import Any
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional


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
    # TODO: https://github.com/python/typeshed/issues/2333
    from typing import cast
    resp = cast(urllib.response.addinfourl, resp)
    return Response(json.load(resp), _parse_link(resp.headers['link']))


def get_all(url: str, **kwargs: Any) -> List[Dict[str, Any]]:
    ret: List[Dict[str, Any]] = []
    resp = req(url, **kwargs)
    ret.extend(resp.json)
    while 'next' in resp.links:
        resp = req(resp.links['next'], **kwargs)
        ret.extend(resp.json)
    return ret


def filter_repos_from_settings(
    repos: List[Dict[str, Any]], settings: Any,
) -> Dict[str, str]:
    return filter_repos(
        repos,
        archived=settings.archived,
    )


def filter_repos(
        repos: List[Dict[str, Any]], *,
        archived: bool,
) -> Dict[str, str]:
    return {
        repo['path_with_namespace']: repo['ssh_url_to_repo']
        for repo in repos
        if (
            archived or not repo['archived']
        )
    }
