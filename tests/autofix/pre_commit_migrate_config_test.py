from __future__ import annotations

from all_repos import clone
from all_repos.autofix.pre_commit_migrate_config import find_repos
from all_repos.autofix.pre_commit_migrate_config import main
from all_repos.config import load_config
from testing.git import write_file_commit


def test_main(file_config, autoupdatable):
    ret = main((
        '--config-filename', str(file_config.cfg),
        '--repos', str(autoupdatable.update_repo),
    ))
    assert not ret

    ret = autoupdatable.consuming_repo.join('.pre-commit-config.yaml').read()
    assert ret == (
        f'repos:\n'
        f'-   repo: {autoupdatable.hook_repo}\n'
        f'    rev: {autoupdatable.hook_repo_rev}\n'
        f'    hooks:\n'
        f'    -   id: hook\n'
    )


def test_find_repos(file_config_files):
    write_file_commit(
        # A migrated configuration
        file_config_files.dir1, '.pre-commit-config.yaml', 'repos: []\n',
    )
    write_file_commit(
        # A non-migrated configuration
        file_config_files.dir2, '.pre-commit-config.yaml', '[]\n',
    )
    clone.main(('--config-filename', str(file_config_files.cfg)))
    ret = find_repos(load_config(str(file_config_files.cfg)))
    assert ret == {str(file_config_files.output_dir.join('repo2'))}
