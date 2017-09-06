import os
import subprocess

import pytest
from pre_commit.constants import VERSION as PRE_COMMIT_VERSION

import testing.git
from all_repos import autofix_lib
from all_repos import git
from all_repos.config import load_config


@pytest.mark.parametrize(
    ('cli_repos', 'expected'),
    (
        (None, ['found_repo']),
        ([], []),
        (['cli_repo'], ['cli_repo']),
    ),
)
def test_filter_repos(cli_repos, expected):
    ret = autofix_lib.filter_repos(None, cli_repos, lambda _: ['found_repo'])
    assert ret == expected


def test_assert_importable_is_importable():
    autofix_lib.assert_importable('pre_commit', install='pre-commit')


def test_assert_importable_not_importable():
    with pytest.raises(SystemExit) as excinfo:
        autofix_lib.assert_importable('watmodule', install='wat')
    msg, = excinfo.value.args
    assert msg == (
        'This tool requires the `watmodule` module to be installed.\n'
        'Try installing it via `pip install wat`.'
    )


def test_require_version_new_enough():
    autofix_lib.require_version_gte('pre-commit', '0.17.0')


def test_require_version_not_new_enough():
    with pytest.raises(SystemExit) as excinfo:
        autofix_lib.require_version_gte('pre-commit', '999')
    msg, = excinfo.value.args
    assert msg == (
        f'This tool requires the `pre-commit` package is at least version '
        f'999.  The currently installed version is {PRE_COMMIT_VERSION}.\n\n'
        f'Try `pip install --upgrade pre-commit`'
    )


def test_run(capfd):
    autofix_lib.run('echo', 'h"i')
    out, _ = capfd.readouterr()
    assert out == (
        '$ echo \'h"i\'\n'
        'h"i\n'
    )


def test_cwd(tmpdir):
    orig = os.getcwd()
    with autofix_lib.cwd(tmpdir):
        assert os.getcwd() == tmpdir
    assert os.getcwd() == orig


def test_repo_context_success(file_config_files, capsys):
    expected_rev = testing.git.revparse(file_config_files.dir1)
    with autofix_lib.repo_context(
            str(file_config_files.output_dir.join('repo1')), use_color=False,
    ):
        assert testing.git.revparse('.') == expected_rev
        assert git.remote('.') == file_config_files.dir1
    out, err = capsys.readouterr()
    assert err == ''
    assert 'Errored' not in out


def test_repo_context_errors(file_config_files, capsys):
    with autofix_lib.repo_context(
            str(file_config_files.output_dir.join('repo1')), use_color=False,
    ):
        assert False
    out, err = capsys.readouterr()
    assert 'Errored' in out
    assert 'assert False' in err


def lower_case_f():
    f_contents = open('f').read()
    with open('f', 'w') as f:
        f.write(f_contents.lower())


def failing_check_fix():
    raise AssertionError('nope!')


def test_fix_dry_run_no_change(file_config_files, capfd):
    autofix_lib.fix(
        (
            str(file_config_files.output_dir.join('repo1')),
            str(file_config_files.output_dir.join('repo2')),
        ),
        apply_fix=lower_case_f,
        config=load_config(file_config_files.cfg),
        commit=autofix_lib.Commit('message!', 'test-branch', None),
        autofix_settings=autofix_lib.AutofixSettings(
            jobs=1, color=False, limit=None, dry_run=True,
        ),
    )

    out, err = capfd.readouterr()
    assert err == ''
    assert 'Errored' not in out
    # Showed the diff of what would have happened
    assert '-OHAI\n+ohai\n' in out
    assert '-OHELLO\n+ohello\n' in out

    # Didn't actually perform any changes
    assert file_config_files.dir1.join('f').read() == 'OHAI\n'
    assert file_config_files.dir2.join('f').read() == 'OHELLO\n'


def test_fix_with_limit(file_config_files, capfd):
    autofix_lib.fix(
        (
            str(file_config_files.output_dir.join('repo1')),
            str(file_config_files.output_dir.join('repo2')),
        ),
        apply_fix=lower_case_f,
        config=load_config(file_config_files.cfg),
        commit=autofix_lib.Commit('message!', 'test-branch', None),
        autofix_settings=autofix_lib.AutofixSettings(
            jobs=1, color=False, limit=1, dry_run=True,
        ),
    )

    out, err = capfd.readouterr()
    assert err == ''
    assert 'Errored' not in out
    # Should still see the diff from the first repository
    assert '-OHAI\n+ohai\n' in out
    assert '-OHELLO\n+ohello\n' not in out


def test_autofix_makes_commits(file_config_files, capfd):
    autofix_lib.fix(
        (
            str(file_config_files.output_dir.join('repo1')),
            str(file_config_files.output_dir.join('repo2')),
        ),
        apply_fix=lower_case_f,
        config=load_config(file_config_files.cfg),
        commit=autofix_lib.Commit('message!', 'test-branch', 'A B <a@a.a>'),
        autofix_settings=autofix_lib.AutofixSettings(
            jobs=1, color=False, limit=None, dry_run=False,
        ),
    )

    out, err = capfd.readouterr()
    assert err == ''
    assert 'Errored' not in out

    assert file_config_files.dir1.join('f').read() == 'ohai\n'
    assert file_config_files.dir2.join('f').read() == 'ohello\n'

    # The branch name should be what we specified
    last_commit_msg = subprocess.check_output((
        'git', '-C', file_config_files.dir1, 'log',
        '--format=%s', '--first-parent', '-1',
    )).decode()
    assert last_commit_msg == "Merge branch 'all-repos_autofix_test-branch'\n"

    # We should see a commit from the autofix change we made
    commit = subprocess.check_output((
        'git', '-C', file_config_files.dir1, 'log',
        '--patch', '--grep', 'message!', '--format=%an %ae\n%B',
    )).decode()
    assert commit.startswith(
        'A B a@a.a\n'
        'message!\n'
        '\n'
        'Committed via https://github.com/asottile/all-repos\n',
    )
    assert commit.endswith('-OHAI\n+ohai\n')


def test_fix_failing_check_no_changes(file_config_files, capfd):
    autofix_lib.fix(
        (
            str(file_config_files.output_dir.join('repo1')),
            str(file_config_files.output_dir.join('repo2')),
        ),
        apply_fix=lower_case_f,
        check_fix=failing_check_fix,
        config=load_config(file_config_files.cfg),
        commit=autofix_lib.Commit('message!', 'test-branch', None),
        autofix_settings=autofix_lib.AutofixSettings(
            jobs=1, color=False, limit=None, dry_run=False,
        ),
    )

    out, err = capfd.readouterr()
    assert 'nope!' in err
    assert out.count('Errored') == 2

    # An error while checking should not allow the changes
    assert file_config_files.dir1.join('f').read() == 'OHAI\n'
    assert file_config_files.dir2.join('f').read() == 'OHELLO\n'


def test_noop_does_not_commit(file_config_files, capfd):
    rev_before1 = testing.git.revparse(file_config_files.dir1)
    rev_before2 = testing.git.revparse(file_config_files.dir2)
    autofix_lib.fix(
        (
            str(file_config_files.output_dir.join('repo1')),
            str(file_config_files.output_dir.join('repo2')),
        ),
        apply_fix=lambda: None,
        config=load_config(file_config_files.cfg),
        commit=autofix_lib.Commit('message!', 'test-branch', None),
        autofix_settings=autofix_lib.AutofixSettings(
            jobs=1, color=False, limit=None, dry_run=False,
        ),
    )
    rev_after1 = testing.git.revparse(file_config_files.dir1)
    rev_after2 = testing.git.revparse(file_config_files.dir2)
    assert (rev_before1, rev_before2) == (rev_after1, rev_after2)
