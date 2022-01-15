from __future__ import annotations

from all_repos import clone
from all_repos.sed import main
from testing.git import commit
from testing.git import write_file_commit


def test_main(file_config_files):
    assert not main((
        '--config-filename', str(file_config_files.cfg),
        's/HAI/BAI/g', '*',
    ))
    assert file_config_files.dir1.join('f').read() == 'OBAI\n'
    assert file_config_files.dir2.join('f').read() == 'OHELLO\n'


def test_main_extended_regexes(file_config_files):
    assert not main((
        '--config-filename', str(file_config_files.cfg),
        '--regexp-extended',
        's/H(A)I/BAI/g', '*',
    ))
    assert file_config_files.dir1.join('f').read() == 'OBAI\n'
    assert file_config_files.dir2.join('f').read() == 'OHELLO\n'


def test_main_ignores_non_files(file_config_files):
    file_config_files.dir1.join('s').mksymlinkto('doesnt_exist')
    commit(file_config_files.dir1)
    test_main(file_config_files)


def test_main_custom_file_pattern(file_config_files):
    write_file_commit(file_config_files.dir1, 'g', 'OHAI\n')
    clone.main(('--config-filename', str(file_config_files.cfg)))
    assert not main((
        '--config-filename', str(file_config_files.cfg),
        's/AI/IE/g', 'g',
    ))
    assert file_config_files.dir1.join('f').read() == 'OHAI\n'
    assert file_config_files.dir1.join('g').read() == 'OHIE\n'
    assert file_config_files.dir2.join('f').read() == 'OHELLO\n'
