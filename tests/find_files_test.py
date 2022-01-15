from __future__ import annotations

from all_repos.find_files import main


def test_find_files(file_config_files, capsys):
    assert not main((
        '-C', str(file_config_files.cfg), '--color=never', r'\d',
    ))
    out, _ = capsys.readouterr()
    assert out == '{}:{}\n'.format(
        file_config_files.output_dir.join('repo2'), 'f2',
    )


def test_find_files_output_paths(file_config_files, capsys):
    assert not main((
        '-C', str(file_config_files.cfg), '--color=never', '--output-paths',
        r'\d',
    ))
    out, _ = capsys.readouterr()
    assert out == '{}\n'.format(file_config_files.output_dir.join('repo2/f2'))


def test_find_files_repos(file_config_files, capsys):
    assert not main((
        '-C', str(file_config_files.cfg), '--color=never', '--repos', r'\d',
    ))
    out, _ = capsys.readouterr()
    assert out == '{}\n'.format(file_config_files.output_dir.join('repo2'))


def test_find_files_not_matching(file_config_files, capsys):
    assert main(('-C', str(file_config_files.cfg), 'g'))
    out, _ = capsys.readouterr()
    assert not out


def test_find_files_repos_not_matching(file_config_files, capsys):
    assert main(('-C', str(file_config_files.cfg), '--repos', 'g'))
    out, _ = capsys.readouterr()
    assert not out
