import json
import urllib.request
from typing import Any
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional


class Response(NamedTuple):
    values: Any
    next: Optional[int]
    links: Optional[Dict[str, Any]]


def req(url: str, **kwargs: Any) -> Response:
    resp = urllib.request.urlopen(urllib.request.Request(url, **kwargs))
    obj = json.load(resp)
    next_index = None
    if obj.get('nextPageStart') is not None and not obj['isLastPage']:
        next_index = obj['nextPageStart']
    return Response(obj.get('values'), next_index, obj.get('links'))


def get_all(url: str, **kwargs: Any) -> List[Dict[str, Any]]:
    ret: List[Dict[str, Any]] = []
    resp = req(url, **kwargs)
    ret.extend(resp.values)
    query_start = '' if '?' in url else '?'
    while resp.next is not None:
        resp = req(f'{url}{query_start}&start={resp.next}', **kwargs)
        ret.extend(resp.values)
    return ret
