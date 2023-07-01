from __future__ import annotations

import os
from typing import Protocol


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


class _SettingsApiKey(Protocol):
    @property
    def api_key(self) -> str | None: ...

    @property
    def api_key_env(self) -> str | None: ...


def load_api_key(settings: _SettingsApiKey) -> str:
    if bool(settings.api_key) == bool(settings.api_key_env):
        raise ValueError('expected exactly one of: api_key, api_key_env')
    elif settings.api_key is not None:
        return settings.api_key
    elif settings.api_key_env is not None:
        if settings.api_key_env not in os.environ:
            raise ValueError(f'api_key_env ({settings.api_key_env}) not set')
        else:
            return os.environ[settings.api_key_env]
    else:
        raise AssertionError('unreachable')
