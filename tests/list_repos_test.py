from __future__ import annotations

from all_repos.list_repos import main


def test_list_repos_main(file_config_files, capsys):
    assert not main(('--config-filename', str(file_config_files.cfg)))
    out, _ = capsys.readouterr()
    assert out == 'repo1\nrepo2\n'


def test_list_repos_with_output_paths(file_config_files, capsys):
    assert not main((
        '--config-filename', str(file_config_files.cfg),
        '--output-paths',
    ))
    out, _ = capsys.readouterr()
    assert out == '{}\n{}\n'.format(
        file_config_files.output_dir.join('repo1'),
        file_config_files.output_dir.join('repo2'),
    )
