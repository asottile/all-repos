from all_repos.list_repos import main


def test_list_repos_main(file_config_files, capsys):
    assert not main(('--config-filename', str(file_config_files.cfg)))
    out, _ = capsys.readouterr()
    assert out == 'repo1\nrepo2\n'
