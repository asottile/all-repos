import collections
import json
import multiprocessing
import subprocess

import pytest

from all_repos.clone import jobs_type
from all_repos.clone import main


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        ('0', multiprocessing.cpu_count()),
        ('-1', multiprocessing.cpu_count()),
        ('1', 1),
        ('2', 2),
    ),
)
def test_jobs_type(s, expected):
    assert jobs_type(s) == expected


def auto_namedtuple(**kwargs):
    return collections.namedtuple('auto_namedtuple', tuple(kwargs))(**kwargs)


def _revparse(pth):
    rev = subprocess.check_output(('git', '-C', pth, 'rev-parse', 'HEAD'))
    return rev.decode().strip()


def _init_repo(pth):
    subprocess.check_call(('git', 'init', pth))
    subprocess.check_call((
        'git', '-C', pth, 'commit', '--allow-empty', '-m', pth,
    ))
    return _revparse(pth)


@pytest.fixture
def file_config(tmpdir):
    dir1 = tmpdir.join('1')
    dir2 = tmpdir.join('2')
    rev1 = _init_repo(dir1)
    rev2 = _init_repo(dir2)

    repos_json = tmpdir.join('repos.json')
    repos_json.write(json.dumps({
        'repo1': dir1.strpath, 'repo2': dir2.strpath,
    }))

    output_dir = tmpdir.join('output')
    cfg = tmpdir.join('config.json')
    cfg.write(json.dumps({
        'output_dir': output_dir.strpath,
        'mod': 'all_repos.sources.json_file',
        'settings': {'filename': repos_json.strpath},
    }))
    cfg.chmod(0o600)
    return auto_namedtuple(
        output_dir=output_dir,
        cfg=cfg,
        repos_json=repos_json,
        dir1=dir1,
        dir2=dir2,
        rev1=rev1,
        rev2=rev2,
        tmp=tmpdir,
    )


def test_clone_file_config(file_config):
    ret = main(('--config-file', file_config.cfg.strpath, '--jobs', '1'))
    assert not ret
    assert file_config.output_dir.isdir()

    expected = {
        'repo1': file_config.dir1.strpath, 'repo2': file_config.dir2.strpath,
    }
    repos = json.loads(file_config.output_dir.join('repos.json').read())
    assert repos == expected
    repos_filtered = file_config.output_dir.join('repos_filtered.json')
    repos_filtered = json.loads(repos_filtered.read())
    assert repos_filtered == expected

    assert file_config.output_dir.join('repo1').isdir()
    assert _revparse(file_config.output_dir.join('repo1')) == file_config.rev1
    assert file_config.output_dir.join('repo2').isdir()
    assert _revparse(file_config.output_dir.join('repo2')) == file_config.rev2

    # Recloning should end up with an updated revision
    subprocess.check_call((
        'git', '-C', file_config.dir1, 'commit', '--allow-empty', '-m', 'foo',
    ))
    new_rev = _revparse(file_config.dir1)
    assert new_rev != file_config.rev1
    ret = main(('--config-file', file_config.cfg.strpath, '--jobs', '1'))
    assert not ret
    assert _revparse(file_config.output_dir.join('repo1')) == new_rev

    # Recloning with a removed directory should remove the repo
    new_contents = json.dumps({'repo2': file_config.dir2.strpath})
    file_config.repos_json.write(new_contents)
    ret = main(('--config-file', file_config.cfg.strpath, '--jobs', '4'))
    assert not ret
    assert not file_config.output_dir.join('repo1').exists()
