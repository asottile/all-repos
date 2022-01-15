from __future__ import annotations

import json
import urllib.request
from typing import Any
from typing import NamedTuple


class Response(NamedTuple):
    values: Any
    next: int | None
    links: dict[str, Any] | None


def req(url: str, **kwargs: Any) -> Response:
    resp = urllib.request.urlopen(urllib.request.Request(url, **kwargs))
    obj = json.load(resp)
    next_index = None
    if obj.get('nextPageStart') is not None and not obj['isLastPage']:
        next_index = obj['nextPageStart']
    return Response(obj.get('values'), next_index, obj.get('links'))


def get_all(url: str, **kwargs: Any) -> list[dict[str, Any]]:
    ret: list[dict[str, Any]] = []
    resp = req(url, **kwargs)
    ret.extend(resp.values)
    query_start = '' if '?' in url else '?'
    while resp.next is not None:
        resp = req(f'{url}{query_start}&start={resp.next}', **kwargs)
        ret.extend(resp.values)
    return ret
