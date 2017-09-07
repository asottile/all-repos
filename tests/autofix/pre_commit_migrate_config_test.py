from all_repos.autofix.pre_commit_migrate_config import main


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
        f'    sha: {autoupdatable.hook_repo_rev}\n'
        f'    hooks:\n'
        f'    -   id: hook\n'
    )
