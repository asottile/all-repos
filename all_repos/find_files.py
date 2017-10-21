import argparse
import os.path
import re
import subprocess
import sys

from all_repos import cli
from all_repos import color
from all_repos.config import load_config
from all_repos.util import zsplit


def ls_files(config, repo):
    path = os.path.join(config.output_dir, repo)
    ret = subprocess.run(
        ('git', '-C', path, 'ls-files', '-z'),
        stdout=subprocess.PIPE, check=True,
    )
    return path, zsplit(ret.stdout)


def find_files(config, regex):
    regex_compiled = re.compile(regex.encode())
    repos = config.get_cloned_repos()
    ret = {}
    for repo in repos:
        repo, filenames = ls_files(config, repo)
        matched = [f for f in filenames if regex_compiled.search(f)]
        if matched:
            ret[repo] = matched
    return ret


def find_files_repos_cli(config, regex, *, use_color):
    repo_files = find_files(config, regex)
    for repo in repo_files:
        print(repo)
    return not repo_files


def find_files_cli(config, regex, *, use_color):
    repo_files = find_files(config, regex)
    for repo, matching in repo_files.items():
        for filename in matching:
            sys.stdout.buffer.write(
                color.fmtb(repo.encode(), color.BLUE_B, use_color=use_color) +
                color.fmtb(b':', color.TURQUOISE, use_color=use_color) +
                filename + b'\n',
            )
    return not repo_files


def main(argv=None):
    parser = argparse.ArgumentParser()
    cli.add_config_arg(parser)
    cli.add_color_arg(parser)
    parser.add_argument(
        '--repos-with-matches', action='store_true',
        help='Only print repositories with matches.',
    )
    parser.add_argument('regex')
    args = parser.parse_args(argv)

    config = load_config(args.config_filename)
    if args.repos_with_matches:
        return find_files_repos_cli(config, args.regex, use_color=args.color)
    else:
        return find_files_cli(config, args.regex, use_color=args.color)


if __name__ == '__main__':
    exit(main())
