from __future__ import annotations

import pytest

from all_repos.source.github_forks import list_repos
from all_repos.source.github_forks import Settings
from testing.mock_http import FakeResponse
from testing.mock_http import urlopen_side_effect


def _resource_bytes(repo_name):
    with open(f'testing/resources/github/{repo_name}.json', 'rb') as f:
        return f.read()


@pytest.fixture
def repos_response(mock_urlopen):
    asottile_url = 'repos/asottile/reorder_python_imports/forks?per_page=100'
    asottile_forks = _resource_bytes('asottile-reorder-python-imports-forks')
    asottile_resp = FakeResponse(asottile_forks)
    mxr_url = 'repos/mxr/reorder_python_imports/forks?per_page=100'
    mxr_forks = _resource_bytes('mxr-reorder-python-imports-forks')
    mxr_resp = FakeResponse(mxr_forks)
    mock_urlopen.side_effect = urlopen_side_effect({
        f'https://api.github.com/{asottile_url}': asottile_resp,
        f'https://api.github.com/{mxr_url}': mxr_resp,
    })


def test_list_repos(repos_response):
    settings = Settings('key', 'asottile/reorder_python_imports')
    ret = list_repos(settings)
    expected = {
        'chriskuehl/reorder_python_imports',
        'mxr/reorder_python_imports',
        'rkm/reorder_python_imports',
    }
    assert set(ret) == expected


def test_settings_repr():
    assert repr(Settings('api_key', 'asottile/foo')) == (
        'Settings(\n'
        '    api_key=...,\n'
        "    repo='asottile/foo',\n"
        '    collaborator=True,\n'
        '    forks=True,\n'
        '    private=False,\n'
        '    archived=False,\n'
        "    base_url='https://api.github.com',\n"
        ')'
    )
