from __future__ import annotations

import json
import urllib.request
from typing import Any
from typing import NamedTuple


class Response(NamedTuple):
    values: Any
    next: str


def req(url: str, **kwargs: Any) -> Response:
    resp = urllib.request.urlopen(urllib.request.Request(url, **kwargs))
    obj = json.load(resp)
    return Response(obj['values'], obj.get('next'))


def get_all(url: str, **kwargs: Any) -> list[dict[str, Any]]:
    ret: list[dict[str, Any]] = []
    resp = req(url, **kwargs)
    ret.extend(resp.values)
    while resp.next is not None:
        resp = req(resp.next, **kwargs)
        ret.extend(resp.values)
    return ret
