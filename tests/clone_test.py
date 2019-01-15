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


def test_it_can_clone_non_master_default_branch(file_config_non_default):
    assert not main(('--config-file', str(file_config_non_default.cfg)))

    repo = file_config_non_default.output_dir.join('repo1')
    cmd = ('git', '-C', repo, 'branch')
    out = subprocess.check_output(cmd).strip().decode()
    assert out == '* m2'
