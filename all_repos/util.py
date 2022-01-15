from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Protocol
else:
    Protocol = object


class NamedTupleProtocol(Protocol):
    @property
    def _fields(self) -> tuple[str, ...]: ...


def hide_api_key_repr(nt: NamedTupleProtocol, *, key: str = 'api_key') -> str:
    fields = ''.join(
        f'    {key}=...,\n'
        if k == key else
        f'    {k}={getattr(nt, k)!r},\n'
        for k in nt._fields
    )
    return f'{type(nt).__name__}(\n{fields})'


def zsplit(bs: bytes) -> list[bytes]:
    if bs:
        return bs.rstrip(b'\0').split(b'\0')
    else:
        return []
