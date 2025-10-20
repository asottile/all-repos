from __future__ import annotations

import os
from unittest import mock

from all_repos import clone
from all_repos.autofix.pre_commit_cache_dir import main
from testing.git import write_file_commit


def test_main(file_config_files):
    write_file_commit(
        file_config_files.dir1, '.travis.yml',
        'language: python\n'
        'matrix:\n'
        '    include:\n'
        '        -   env: TOXENV=py36\n'
        '            python: 3.6\n'
        'install: pip install coveralls tox\n'
        'script: tox\n'
        'after_success: coveralls\n'
        'cache:\n'
        '    directories:\n'
        '        - $HOME/.cache/pip\n'
        '        - $HOME/.pre-commit\n',
    )
    write_file_commit(
        file_config_files.dir2, 'appveyor.yml',
        r'environment:\n'
        r'    matrix:\n'
        r'        - TOXENV: py36\n'
        r'install:\n'
        r'    - "SET PATH=C:\\Python36;C:\\Python36\\Scripts;%PATH%"\n'
        r'    - pip install tox\n'
        r'build: false\n'
        r'test_script: tox\n'
        r'cache:\n'
        r"  - '%LOCALAPPDATA%\pip\cache'\n"
        r"  - '%USERPROFILE%\.pre-commit'\n",
    )

    clone.main(('--config-filename', str(file_config_files.cfg)))
    assert not main(('--config-filename', str(file_config_files.cfg)))

    assert file_config_files.dir1.join('.travis.yml').read() == (
        'language: python\n'
        'matrix:\n'
        '    include:\n'
        '        -   env: TOXENV=py36\n'
        '            python: 3.6\n'
        'install: pip install coveralls tox\n'
        'script: tox\n'
        'after_success: coveralls\n'
        'cache:\n'
        '    directories:\n'
        '        - $HOME/.cache/pip\n'
        '        - $HOME/.cache/pre-commit\n'
    )
    assert file_config_files.dir2.join('appveyor.yml').read() == (
        r'environment:\n'
        r'    matrix:\n'
        r'        - TOXENV: py36\n'
        r'install:\n'
        r'    - "SET PATH=C:\\Python36;C:\\Python36\\Scripts;%PATH%"\n'
        r'    - pip install tox\n'
        r'build: false\n'
        r'test_script: tox\n'
        r'cache:\n'
        r"  - '%LOCALAPPDATA%\pip\cache'\n"
        r"  - '%USERPROFILE%\.cache\pre-commit'\n"
    )


def test_with_extended_regexp(file_config_files):
    git_env = {
        'GIT_CONFIG_COUNT': '1',
        'GIT_CONFIG_KEY_0': 'grep.extendedRegexp',
        'GIT_CONFIG_VALUE_0': 'true',
    }
    with mock.patch.dict(os.environ, git_env):
        test_main(file_config_files)
