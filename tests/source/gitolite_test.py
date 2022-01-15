from __future__ import annotations

import json
import subprocess
from unittest import mock

import pytest

from all_repos.source import gitolite


@pytest.fixture
def settings():
    return gitolite.Settings(
        username='git',
        hostname='git.mycompany.com',
    )


def test_clone_url_default(settings):
    assert settings.clone_url('some_package') == (
        'git@git.mycompany.com:some_package'
    )
    assert settings.clone_url('some/nested/package') == (
        'git@git.mycompany.com:some/nested/package'
    )


def test_clone_url_custom_mirror_path(settings):
    settings = settings._replace(
        mirror_path='/gitolite/git/{repo_name}.git',
    )
    assert settings.clone_url('some_package') == (
        '/gitolite/git/some_package.git'
    )
    assert settings.clone_url('some/nested/package') == (
        '/gitolite/git/some/nested/package.git'
    )


@pytest.fixture
def fake_info_response():
    response = json.dumps({
        'repos': {
            'some_rw_repo': {
                'perms': {'R': 1, 'W': 1},
            },
            'some_ro_repo': {
                'perms': {'R': 1},
            },
        },
        'gitolite_version': '1.2.3',
        'USER': 'git@somehost',
        'GL_USER': 'someuser',
        'git_version': '1.2.3',
    }).encode()

    side_effect = {
        ('ssh', 'git@git.mycompany.com', 'info', '-json'): response,
    }.__getitem__

    with mock.patch.object(
            subprocess, 'check_output', side_effect=side_effect,
    ):
        yield


@pytest.mark.usefixtures('fake_info_response')
def test_repo_names_from_source(settings):
    assert gitolite._repo_names_from_source(settings) == {
        'some_rw_repo', 'some_ro_repo',
    }


@pytest.mark.usefixtures('fake_info_response')
def test_list_repos(settings):
    assert gitolite.list_repos(settings) == {
        'some_rw_repo.git': 'git@git.mycompany.com:some_rw_repo',
        'some_ro_repo.git': 'git@git.mycompany.com:some_ro_repo',
    }
