import json
import urllib.request
from typing import Any
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from typing import Protocol
else:
    Protocol = object


class NamedTupleProtocol(Protocol):
    @property
    def _fields(self) -> Tuple[str, ...]: ...


def hide_api_key_repr(nt: NamedTupleProtocol, *, key: str = 'api_key') -> str:
    fields = ''.join(
        f'    {key}=...,\n'
        if k == key else
        f'    {k}={getattr(nt, k)!r},\n'
        for k in nt._fields
    )
    return f'{type(nt).__name__}(\n{fields})'


def zsplit(bs: bytes) -> List[bytes]:
    if bs:
        return bs.rstrip(b'\0').split(b'\0')
    else:
        return []


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
