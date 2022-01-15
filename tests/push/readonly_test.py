from __future__ import annotations

from all_repos.push import readonly


def test_does_not_fire_missiles():
    # does nothing, assert it doesn't crash
    readonly.push(readonly.Settings(), 'branch')
