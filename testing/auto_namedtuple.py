from __future__ import annotations

import collections


def auto_namedtuple(**kwargs):
    return collections.namedtuple('auto_namedtuple', tuple(kwargs))(**kwargs)
