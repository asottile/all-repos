from __future__ import annotations

import pytest

import all_repos.source.json_file
from all_repos import clone
from all_repos.config import load_config


def test_load_config(file_config):
    cfg = load_config(file_config.cfg)
    assert cfg.list_repos is all_repos.source.json_file.list_repos


def test_load_config_too_permissive(file_config):
    file_config.cfg.chmod(0o777)
    with pytest.raises(SystemExit) as excinfo:
        load_config(file_config.cfg)
    msg, = excinfo.value.args
    assert msg == (
        f'{file_config.cfg} has too-permissive permissions, Expected 0o600, '
        f'got 0o777'
    )


def test_get_cloned_repos(file_config):
    clone.main(('--config-filename', str(file_config.cfg)))
    cfg = load_config(file_config.cfg)
    ret = set(cfg.get_cloned_repos())
    assert ret == {'repo1', 'repo2'}
