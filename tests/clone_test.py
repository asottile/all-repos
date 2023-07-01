from __future__ import annotations

import json
import subprocess

from all_repos.clone import main
from testing.git import revparse


def test_it_clones(file_config):
    assert not main(('--config-file', str(file_config.cfg)))
    assert file_config.output_dir.isdir()

    expected = {'repo1': str(file_config.dir1), 'repo2': str(file_config.dir2)}
    repos = json.loads(file_config.output_dir.join('repos.json').read())
    assert repos == expected
    repos_filtered = file_config.output_dir.join('repos_filtered.json')
    repos_filtered = json.loads(repos_filtered.read())
    assert repos_filtered == expected

    assert file_config.output_dir.join('repo1').isdir()
    assert revparse(file_config.output_dir.join('repo1')) == file_config.rev1
    assert file_config.output_dir.join('repo2').isdir()
    assert revparse(file_config.output_dir.join('repo2')) == file_config.rev2


def test_it_does_not_crash_with_no_repos(file_config):
    cfg = json.loads(file_config.cfg.read())
    cfg['include'] = '^$'
    file_config.cfg.write(json.dumps(cfg))
    assert not main(('--config-file', str(file_config.cfg)))


def test_it_updates(file_config):
    assert not main(('--config-file', str(file_config.cfg)))

    # Recloning should end up with an updated revision
    subprocess.check_call((
        'git', '-C', file_config.dir1, 'commit', '--allow-empty', '-m', 'foo',
    ))
    new_rev = revparse(file_config.dir1)
    assert new_rev != file_config.rev1
    assert not main(('--config-file', str(file_config.cfg)))
    assert revparse(file_config.output_dir.join('repo1')) == new_rev


def test_it_removes_directories(file_config):
    assert not main(('--config-file', str(file_config.cfg)))

    # Recloning with a removed directory should remove the repo
    new_contents = json.dumps({'repo2': str(file_config.dir2)})
    file_config.repos_json.write(new_contents)
    assert not main(('--config-file', str(file_config.cfg)))
    assert not file_config.output_dir.join('repo1').exists()


def test_it_removes_empty_directories(file_config):
    new_contents = json.dumps({'dir1/repo2': str(file_config.dir2)})
    file_config.repos_json.write(new_contents)
    assert not main(('--config-file', str(file_config.cfg)))
    assert file_config.output_dir.join('dir1/repo2').isdir()

    new_contents = json.dumps({'repo1': str(file_config.dir1)})
    file_config.repos_json.write(new_contents)
    assert not main(('--config-file', str(file_config.cfg)))

    assert not file_config.output_dir.join('dir1/repo2').exists()
    assert not file_config.output_dir.join('dir1').exists()


def test_it_continues_on_unclonable_repositories(file_config, capsys):
    new_contents = json.dumps({'dir1/repo2': '/does/not/exist'})
    file_config.repos_json.write(new_contents)
    assert not main(('--config-file', str(file_config.cfg)))

    out, err = capsys.readouterr()
    assert 'Error fetching ' in out


def test_it_can_clone_non_main_default_branch(file_config_non_default):
    assert not main(('--config-file', str(file_config_non_default.cfg)))

    repo = file_config_non_default.output_dir.join('repo1')
    cmd = ('git', '-C', repo, 'branch')
    out = subprocess.check_output(cmd).strip().decode()
    assert out == '* m2'


def test_no_crash_repo_without_branch(file_config):
    file_config.dir1.remove()
    # this repo does not have a default branch, or any for that matter
    subprocess.check_call(('git', 'init', file_config.dir1))

    # should not crash
    assert not main(('--config-filename', str(file_config.cfg)))


def test_clones_all_branches_true(file_config):
    subprocess.check_call((
        'git', '-C', str(file_config.dir1), 'checkout', 'main', '-b', 'b2',
    ))
    subprocess.check_call((
        'git', '-C', str(file_config.dir1), 'checkout', 'main',
    ))

    assert not main(('--config-file', str(file_config.cfg)))

    # initially we should not see multiple branches
    branch_out = subprocess.check_output((
        'git', '-C', str(file_config.output_dir.join('repo1')),
        'branch', '--remote',
    )).decode()
    assert branch_out == '  origin/main\n'

    # set that we want to clone all branches
    cfg_contents = json.loads(file_config.cfg.read())
    cfg_contents['all_branches'] = True
    file_config.cfg.write(json.dumps(cfg_contents))

    assert not main(('--config-file', str(file_config.cfg)))

    branch_out = subprocess.check_output((
        'git', '-C', str(file_config.output_dir.join('repo1')),
        'branch', '--remote',
    )).decode()
    assert branch_out == '  origin/b2\n  origin/main\n'


def test_it_sorts_filtered_repos(file_config):
    # make the repos json out of order
    contents = json.loads(file_config.repos_json.read())
    new_contents = json.dumps(dict(reversed(contents.items())))
    file_config.repos_json.write(new_contents)

    assert not main(('--config-file', str(file_config.cfg)))

    repos_filtered = file_config.output_dir.join('repos_filtered.json')
    repos_filtered = json.loads(repos_filtered.read())
    assert sorted(repos_filtered) == list(repos_filtered)
