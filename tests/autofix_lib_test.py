from __future__ import annotations

import os
import subprocess
from unittest import mock

import pytest
from pre_commit.constants import VERSION as PRE_COMMIT_VERSION

import testing.git
from all_repos import autofix_lib
from all_repos import clone
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
def test_filter_repos(file_config, cli_repos, expected):
    ret = autofix_lib.filter_repos(
        file_config, cli_repos, lambda _: ['found_repo'],
    )
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


def test_interactive_control_c(mock_input, capfd):
    mock_input.set_side_effect(KeyboardInterrupt)
    with pytest.raises(SystemExit):
        autofix_lib._interactive_check(use_color=False)
    out, _ = capfd.readouterr()
    assert out == (
        '***Looks good [y,n,s,q,?]? ^C\n'
        'Goodbye!\n'
    )


def test_interactive_eof(mock_input, capfd):
    mock_input.set_side_effect(EOFError)
    with pytest.raises(SystemExit):
        autofix_lib._interactive_check(use_color=False)
    out, _ = capfd.readouterr()
    assert out == (
        '***Looks good [y,n,s,q,?]? ^D\n'
        'Goodbye!\n'
    )


def test_interactive_quit(mock_input, capfd):
    mock_input.set_side_effect('q')
    with pytest.raises(SystemExit):
        autofix_lib._interactive_check(use_color=False)
    out, _ = capfd.readouterr()
    assert out == (
        '***Looks good [y,n,s,q,?]? <<q\n'
        'Goodbye!\n'
    )


def test_interactive_yes(mock_input, capfd):
    mock_input.set_side_effect('y')
    assert autofix_lib._interactive_check(use_color=False) is True
    out, _ = capfd.readouterr()
    assert out == '***Looks good [y,n,s,q,?]? <<y\n'


def test_interactive_no(mock_input, capfd):
    mock_input.set_side_effect('n')
    assert autofix_lib._interactive_check(use_color=False) is False
    out, _ = capfd.readouterr()
    assert out == '***Looks good [y,n,s,q,?]? <<n\n'


def test_interactive_shell(mock_input, capfd):
    mock_input.set_side_effect('s', 'n')
    with mock.patch.dict(os.environ, {'SHELL': 'echo'}):
        assert autofix_lib._interactive_check(use_color=False) is False
    out, _ = capfd.readouterr()
    assert out == (
        '***Looks good [y,n,s,q,?]? <<s\n'
        'Opening an interactive shell, type `exit` to continue.\n'
        'Any modifications will be committed.\n'
        # A newline from echo
        '\n'
        '***Looks good [y,n,s,q,?]? <<n\n'
    )


def test_interactive_help(mock_input, capfd):
    mock_input.set_side_effect('?', 'n')
    assert autofix_lib._interactive_check(use_color=False) is False
    out, _ = capfd.readouterr()
    assert out == (
        '***Looks good [y,n,s,q,?]? <<?\n'
        'y (yes): yes it looks good, commit and continue.\n'
        'n (no): no, do not commit this repository.\n'
        's (shell): open an interactive shell in the repo.\n'
        'q (quit, ^C): early exit from the autofixer.\n'
        '? (help): show this help message.\n'
        '***Looks good [y,n,s,q,?]? <<n\n'
    )


def test_interactive_garbage(mock_input, capfd):
    mock_input.set_side_effect('garbage', 'n')
    assert autofix_lib._interactive_check(use_color=False) is False
    out, _ = capfd.readouterr()
    assert out == (
        '***Looks good [y,n,s,q,?]? <<garbage\n'
        'Unexpected input: garbage\n'
        'y (yes): yes it looks good, commit and continue.\n'
        'n (no): no, do not commit this repository.\n'
        's (shell): open an interactive shell in the repo.\n'
        'q (quit, ^C): early exit from the autofixer.\n'
        '? (help): show this help message.\n'
        '***Looks good [y,n,s,q,?]? <<n\n'
    )


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
            jobs=1, color=False, limit=None, dry_run=True, interactive=False,
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
            jobs=1, color=False, limit=1, dry_run=True, interactive=False,
        ),
    )

    out, err = capfd.readouterr()
    assert err == ''
    assert 'Errored' not in out
    # Should still see the diff from the first repository
    assert '-OHAI\n+ohai\n' in out
    assert '-OHELLO\n+ohello\n' not in out


def test_fix_interactive(file_config_files, capfd, mock_input):
    mock_input.set_side_effect('y', 'n')
    autofix_lib.fix(
        (
            str(file_config_files.output_dir.join('repo1')),
            str(file_config_files.output_dir.join('repo2')),
        ),
        apply_fix=lower_case_f,
        config=load_config(file_config_files.cfg),
        commit=autofix_lib.Commit('message!', 'test-branch', None),
        autofix_settings=autofix_lib.AutofixSettings(
            jobs=1, color=False, limit=None, dry_run=False, interactive=True,
        ),
    )

    assert file_config_files.dir1.join('f').read() == 'ohai\n'
    assert file_config_files.dir2.join('f').read() == 'OHELLO\n'


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
            jobs=1, color=False, limit=None, dry_run=False, interactive=False,
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
    )).strip().decode()
    potential_msgs = testing.git.merge_msgs('all-repos_autofix_test-branch')
    assert last_commit_msg in potential_msgs

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
            jobs=1, color=False, limit=None, dry_run=False, interactive=False,
        ),
    )

    out, err = capfd.readouterr()
    assert 'nope!' in err
    assert out.count('Errored') == 2

    # An error while checking should not allow the changes
    assert file_config_files.dir1.join('f').read() == 'OHAI\n'
    assert file_config_files.dir2.join('f').read() == 'OHELLO\n'


def test_noop_does_not_commit(file_config_files):
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
            jobs=1, color=False, limit=None, dry_run=False, interactive=False,
        ),
    )
    rev_after1 = testing.git.revparse(file_config_files.dir1)
    rev_after2 = testing.git.revparse(file_config_files.dir2)
    assert (rev_before1, rev_before2) == (rev_after1, rev_after2)


def test_fix_non_default_branch(file_config_non_default):
    clone.main(('--config-filename', str(file_config_non_default.cfg)))

    autofix_lib.fix(
        (
            str(file_config_non_default.output_dir.join('repo1')),
        ),
        apply_fix=lower_case_f,
        config=load_config(file_config_non_default.cfg),
        commit=autofix_lib.Commit('message!', 'test-branch', 'A B <a@a.a>'),
        autofix_settings=autofix_lib.AutofixSettings(
            jobs=1, color=False, limit=None, dry_run=False, interactive=False,
        ),
    )

    assert file_config_non_default.dir1.join('f').read() == 'ohai\n'
