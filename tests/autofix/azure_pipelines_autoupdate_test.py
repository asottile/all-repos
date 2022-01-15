from __future__ import annotations

import subprocess
from unittest import mock

import pytest

from all_repos import clone
from all_repos.autofix import azure_pipelines_autoupdate
from all_repos.config import load_config
from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo
from testing.git import write_file_commit


@pytest.fixture
def fake_clone(tmpdir_factory):
    src = tmpdir_factory.mktemp('repo')
    init_repo(src)
    write_file_commit(src, 'job--pre-commit.yml', 'jobs: []')
    subprocess.check_call(('git', '-C', src, 'tag', 'v1.0.0'))
    write_file_commit(src, 'README.md', '# template repo')

    def clone_func(service, repo, path):
        subprocess.check_call(('git', 'clone', src, path))
        subprocess.check_call(('git', 'fetch', 'origin', 'HEAD'), cwd=path)

    with mock.patch.object(azure_pipelines_autoupdate, '_clone', clone_func):
        yield


SAMPLE = '''\
resources:
  repositories:
    - repository: self
      checkoutOptions:
        submodules: true
    - repository: asottile
      type: github
      endpoint: github
      # formatting comment
      name: asottile/azure-pipeline-templates
      ref: refs/tags/v0.0.1  # line comment
    - repository: asottile
      type: github
      endpoint: github
      name: asottile/azure-pipeline-templates
      ref: refs/tags/v0.0.1
jobs:
- template: job--pre-commit.yml@asottile
'''


@pytest.fixture
def repo(tmpdir):
    src_repo = tmpdir.join('hook_repo')
    init_repo(src_repo)
    write_file_commit(src_repo, 'azure-pipelines.yml', SAMPLE)

    update_repo = tmpdir.join('update_repo')
    subprocess.check_call(('git', 'clone', src_repo, update_repo))

    return auto_namedtuple(src_repo=src_repo, update_repo=update_repo)


def test_clone(tmpdir):
    repo = tmpdir.join('repo')
    azure_pipelines_autoupdate._clone('github', 'asottile/astpretty', repo)
    rev = subprocess.check_output(('git', 'rev-parse', 'v1.7.0'), cwd=repo)
    assert rev.strip().decode() == '1bdab8a7e9c9591669e91de5c1c9584db7267ec6'


@pytest.mark.usefixtures('fake_clone')
def test_basic_rewrite(file_config, repo):
    ret = azure_pipelines_autoupdate.main((
        '--config-filename', str(file_config.cfg),
        '--repos', str(repo.update_repo),
    ))
    assert not ret

    expected = '''\
resources:
  repositories:
    - repository: self
      checkoutOptions:
        submodules: true
    - repository: asottile
      type: github
      endpoint: github
      # formatting comment
      name: asottile/azure-pipeline-templates
      ref: refs/tags/v1.0.0  # line comment
    - repository: asottile
      type: github
      endpoint: github
      name: asottile/azure-pipeline-templates
      ref: refs/tags/v1.0.0
jobs:
- template: job--pre-commit.yml@asottile
'''
    assert repo.src_repo.join('azure-pipelines.yml').read() == expected


def test_find_repos_finds_a_repo(file_config_files):
    write_file_commit(file_config_files.dir1, 'azure-pipelines.yml', SAMPLE)
    clone.main(('--config-filename', str(file_config_files.cfg)))
    config = load_config(str(file_config_files.cfg))
    ret = azure_pipelines_autoupdate.find_repos(config)
    assert ret == {str(file_config_files.output_dir.join('repo1'))}
