from __future__ import annotations

from unittest import mock

from all_repos import autofix_lib
from all_repos import manual


def test_main(file_config_files, mock_input):
    # `manual` drops into interactive mode, accept one and deny the other
    mock_input.set_side_effect('y', 'n')

    def append_to_f():
        with open('f', 'a+') as f:
            f.write('manual\n')

    # simulate a user operation in the "SHELL"
    with mock.patch.object(autofix_lib, 'shell', append_to_f):
        manual.main((
            '--config-filename', str(file_config_files.cfg),
            '--branch-name', 'test-manual',
            '--commit-msg', 'manually edit f',
            '--repos',
            str(file_config_files.output_dir.join('repo1')),
            str(file_config_files.output_dir.join('repo2')),
        ))

    assert file_config_files.dir1.join('f').read() == 'OHAI\nmanual\n'
    assert file_config_files.dir2.join('f').read() == 'OHELLO\n'
