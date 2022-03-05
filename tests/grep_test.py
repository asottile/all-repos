from __future__ import annotations

import sys
from unittest import mock

import pytest

from all_repos.config import load_config
from all_repos.grep import grep
from all_repos.grep import main
from all_repos.grep import repos_matching


def test_repos_matching(file_config_files):
    config = load_config(file_config_files.cfg)
    ret = repos_matching(config, ['^OH'])
    assert ret == {
        file_config_files.output_dir.join('repo1'),
        file_config_files.output_dir.join('repo2'),
    }
    ret = repos_matching(config, ['^OHAI'])
    assert ret == {file_config_files.output_dir.join('repo1')}
    ret = repos_matching(config, ['nope'])
    assert ret == set()


def test_repos_matching_cli(file_config_files, capsys):
    ret = main((
        '-C', str(file_config_files.cfg), '--repos-with-matches', '^OH',
    ))
    assert ret == 0
    out, _ = capsys.readouterr()
    assert out == '{}\n{}\n'.format(
        file_config_files.output_dir.join('repo1'),
        file_config_files.output_dir.join('repo2'),
    )

    ret = main((
        '-C', str(file_config_files.cfg), '--repos-with-matches', 'OHAI',
    ))
    assert ret == 0
    out, _ = capsys.readouterr()
    assert out == '{}\n'.format(file_config_files.output_dir.join('repo1'))

    ret = main((
        '-C', str(file_config_files.cfg), '--repos-with-matches', 'nope',
    ))
    assert ret == 1
    out, _ = capsys.readouterr()
    assert out == ''


def test_grep(file_config_files):
    config = load_config(file_config_files.cfg)
    ret = grep(config, ['^OH'])
    assert ret == {
        file_config_files.output_dir.join('repo1'): b'f:OHAI\n',
        file_config_files.output_dir.join('repo2'): b'f:OHELLO\n',
    }
    ret = grep(config, ['^OHAI'])
    assert ret == {file_config_files.output_dir.join('repo1'): b'f:OHAI\n'}
    ret = grep(config, ['nope'])
    assert ret == {}


def test_grep_cli(file_config_files, capsys):
    ret = main(('-C', str(file_config_files.cfg), '^OH'))
    assert ret == 0
    out, _ = capsys.readouterr()
    assert out == '{}:f:OHAI\n{}:f:OHELLO\n'.format(
        file_config_files.output_dir.join('repo1'),
        file_config_files.output_dir.join('repo2'),
    )

    ret = main(('-C', str(file_config_files.cfg), '^OHAI'))
    assert ret == 0
    out, _ = capsys.readouterr()
    assert out == '{}:f:OHAI\n'.format(
        file_config_files.output_dir.join('repo1'),
    )

    ret = main(('-C', str(file_config_files.cfg), 'nope'))
    assert ret == 1
    out, _ = capsys.readouterr()
    assert out == ''

    ret = main(('-C', str(file_config_files.cfg), '-h', '^OH'))
    assert ret == 0
    out, _ = capsys.readouterr()
    assert out == '{}:OHAI\n{}:OHELLO\n'.format(
        file_config_files.output_dir.join('repo1'),
        file_config_files.output_dir.join('repo2'),
    )


def test_grep_cli_output_paths(file_config_files, capsys):
    cmd = ('-C', str(file_config_files.cfg), '-l', '^OH', '--output-paths')
    assert not main(cmd)
    out, _ = capsys.readouterr()
    assert out == '{}\n{}\n'.format(
        file_config_files.output_dir.join('repo1/f'),
        file_config_files.output_dir.join('repo2/f'),
    )


def _test_grep_color(file_config_files, capsys, *, args=()):
    ret = main(('-C', str(file_config_files.cfg), 'OHAI', *args))
    assert ret == 0
    out, _ = capsys.readouterr()
    directory = file_config_files.output_dir.join('repo1')
    assert out in {
        (
            f'\033[1;34m{directory}\033[m'
            f'\033[36m:\033[m'
            f'\033[35mf\033[m'
            f'\033[36m:\033[m'
            f'\033[1;31mOHAI\033[m\n'
        ),
        (
            f'\033[1;34m{directory}\033[m'
            f'\033[36m:\033[m'
            f'f'
            f'\033[36m:\033[m'
            f'\033[1;31mOHAI\033[m\n'
        ),
    }


def test_grep_color_always(file_config_files, capsys):
    _test_grep_color(file_config_files, capsys, args=('--color', 'always'))


def test_grep_color_tty(file_config_files, capsys):
    with mock.patch.object(sys.stdout, 'isatty', return_value=True):
        _test_grep_color(file_config_files, capsys)


@pytest.mark.parametrize('args', ((), ('--repos-with-matches',)))
def test_grep_error(file_config_files, capfd, args):
    ret = main(('-C', str(file_config_files.cfg), *args))
    assert ret == 128
    out, err = capfd.readouterr()
    assert out == ''
    assert err in {
        'fatal: no pattern given.\n',  # git < v2.19.0-rc0
        'fatal: no pattern given\n',  # git >= v2.19.0-rc0
    }
