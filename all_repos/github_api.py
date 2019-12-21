"""
Copyright (c) 2017 Anthony Sottile
Co-authored by CodingSpiderFox: 2019

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

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
    print(f'Getting URL {url}')
    ret: List[Dict[str, Any]] = []
    resp = req(url, **kwargs)
    ret.extend(resp.json)
    while 'next' in resp.links:
        resp = req(resp.links['next'], **kwargs)
        ret.extend(resp.json)
    return ret


def filter_repos(
        repos: List[Dict[str, Any]], *,
        forks: bool, private: bool, collaborator: bool, archived: bool,
) -> Dict[str, str]:
    return {
        repo['full_name']: 'git@github.com:{}'.format(repo['full_name'])
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
