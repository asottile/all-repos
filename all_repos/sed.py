import argparse
import functools
import os.path
import shlex
import subprocess

from all_repos import autofix_lib
from all_repos import cli
from all_repos.util import zsplit


def find_repos(config, *, ls_files_cmd):
    for repo in config.get_cloned_repos():
        repo_dir = os.path.join(config.output_dir, repo)
        if subprocess.run(
            ('git', '-C', repo_dir, *ls_files_cmd[1:]),
            check=True, stdout=subprocess.PIPE,
        ).stdout:
            yield repo_dir


def apply_fix(*, ls_files_cmd, sed_cmd):
    filenames = zsplit(subprocess.check_output(ls_files_cmd))
    filenames = [f.decode() for f in filenames]
    autofix_lib.run(*sed_cmd, *filenames)


def _quote_cmd(cmd):
    return ' '.join(shlex.quote(arg) for arg in cmd)


def main(argv=None):
    parser = argparse.ArgumentParser()
    cli.add_fixer_args(parser)
    parser.add_argument(
        '-r', '--regexp-extended',
        action='store_true',
        help='use extended regular expressions in the script.',
    )
    parser.add_argument('--branch-name', default='all-repos-sed')
    parser.add_argument('--commit-msg')
    parser.add_argument('pattern')
    parser.add_argument('filenames_glob', help='(passed to ls-files)')
    args = parser.parse_args(argv)

    dash_r = ('-r',) if args.regexp_extended else ()
    sed_cmd = ('sed', '-i', *dash_r, args.pattern)
    ls_files_cmd = ('git', 'ls-files', '-z', '--', args.filenames_glob)

    msg = f'{_quote_cmd(ls_files_cmd)} | xargs -0 {_quote_cmd(sed_cmd)}'
    msg = args.commit_msg or msg

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=functools.partial(find_repos, ls_files_cmd=ls_files_cmd),
        msg=msg, branch_name=args.branch_name,
    )

    autofix_lib.fix(
        repos,
        apply_fix=functools.partial(
            apply_fix, ls_files_cmd=ls_files_cmd, sed_cmd=sed_cmd,
        ),
        config=config, commit=commit, autofix_settings=autofix_settings,
    )


if __name__ == '__main__':
    exit(main())
