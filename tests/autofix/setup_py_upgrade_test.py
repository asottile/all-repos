from __future__ import annotations

import subprocess

import pytest

from all_repos import clone
from all_repos.autofix.setup_py_upgrade import find_repos
from all_repos.autofix.setup_py_upgrade import main
from all_repos.config import load_config
from testing.auto_namedtuple import auto_namedtuple
from testing.git import init_repo
from testing.git import write_file_commit


@pytest.fixture
def setup_py_repo(tmpdir):
    src_repo = tmpdir.join('hook_repo')
    init_repo(src_repo)
    src_repo.join('setup.cfg').write('[bdist_wheel]\nuniversal = true\n')
    write_file_commit(
        src_repo, 'setup.py',
        'from setuptools import setup\n'
        'setup(name="pkg", version="1.0")\n',
    )

    update_repo = tmpdir.join('update_repo')
    subprocess.check_call(('git', 'clone', src_repo, update_repo))

    return auto_namedtuple(src_repo=src_repo, update_repo=update_repo)


def test_basic_rewrite(file_config, setup_py_repo):
    ret = main((
        '--config-filename', str(file_config.cfg),
        '--repos', str(setup_py_repo.update_repo),
    ))
    assert not ret

    setup_py = setup_py_repo.src_repo.join('setup.py').read()
    assert setup_py == 'from setuptools import setup\nsetup()\n'
    setup_cfg = setup_py_repo.src_repo.join('setup.cfg').read()
    assert setup_cfg == (
        '[metadata]\n'
        'name = pkg\n'
        'version = 1.0\n'
        '\n'
        '[bdist_wheel]\n'
        'universal = true\n'
    )


def test_rewrite_setup_cfg_fmt(file_config, setup_py_repo):
    write_file_commit(setup_py_repo.src_repo, 'README.md', 'my project!')
    ret = main((
        '--config-filename', str(file_config.cfg),
        '--repos', str(setup_py_repo.update_repo),
    ))
    assert not ret

    setup_py = setup_py_repo.src_repo.join('setup.py').read()
    assert setup_py == 'from setuptools import setup\nsetup()\n'
    setup_cfg = setup_py_repo.src_repo.join('setup.cfg').read()
    assert setup_cfg == (
        '[metadata]\n'
        'name = pkg\n'
        'version = 1.0\n'
        'long_description = file: README.md\n'
        'long_description_content_type = text/markdown\n'
        '\n'
        '[bdist_wheel]\n'
        'universal = true\n'
    )


def test_find_repos_skips_already_migrated(file_config_files):
    write_file_commit(
        file_config_files.dir1, 'setup.py',
        'from setuptools import setup\nsetup()\n',
    )
    clone.main(('--config-filename', str(file_config_files.cfg)))
    assert find_repos(load_config(str(file_config_files.cfg))) == set()


def test_find_repos_finds_a_repo(file_config_files):
    write_file_commit(
        file_config_files.dir1, 'setup.py',
        'from setuptools import setup\nsetup(name="pkg", version="1")\n',
    )
    clone.main(('--config-filename', str(file_config_files.cfg)))
    ret = find_repos(load_config(str(file_config_files.cfg)))
    assert ret == {str(file_config_files.output_dir.join('repo1'))}
