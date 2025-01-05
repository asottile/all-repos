from __future__ import annotations

import argparse
import os.path
import subprocess
import sys
from collections.abc import Sequence

from all_repos import cli
from all_repos import color
from all_repos.config import Config
from all_repos.config import load_config


class GrepError(ValueError):
    pass


def grep_result(
        config: Config,
        repo: str,
        args: Sequence[str],
) -> tuple[str, int, bytes]:
    path = os.path.join(config.output_dir, repo)
    ret = subprocess.run(
        ('git', '-C', path, 'grep', *args), stdout=subprocess.PIPE,
    )
    return path, ret.returncode, ret.stdout


def grep(config: Config, grep_args: Sequence[str]) -> dict[str, bytes]:
    repos = config.get_cloned_repos()
    ret = {}
    for repo in repos:
        repo, returncode, stdout = grep_result(config, repo, grep_args)
        if returncode == 0:
            ret[repo] = stdout
        elif returncode != 1:
            raise GrepError(returncode)
    return ret


def repos_matching(config: Config, grep_args: Sequence[str]) -> set[str]:
    return set(grep(config, ('--quiet', *grep_args)))

def repos_not_matching(config: Config, grep_args: Sequence[str]) -> set[str]:
    grep_ret = set(grep(config, ('--quiet', *grep_args)))
    repos = [os.path.join(config.output_dir, repo) for repo in config.get_cloned_repos()]

    return set(repos).difference(grep_ret)


def repos_matching_cli(config: Config, grep_args: Sequence[str]) -> int:
    try:
        matching = repos_matching(config, grep_args)
    except GrepError as e:
        return e.args[0]
    for repo in sorted(matching):
        print(repo)
    return int(not matching)


def repos_not_matching_cli(config: Config, grep_args: Sequence[str]) -> int:
    try:
        not_matching = repos_not_matching(config, grep_args)
    except GrepError as e:
        return e.args[0]
    for repo in sorted(not_matching):
        print(repo)
    return int(not not_matching)


def grep_cli(
        config: Config,
        grep_args: Sequence[str],
        *,
        output_paths: bool,
        use_color: bool,
) -> int:
    sep = os.sep.encode() if output_paths else b':'
    if use_color:
        grep_args = ('--color=always', *grep_args)
    try:
        matching = grep(config, grep_args)
    except GrepError as e:
        return e.args[0]
    for repo, stdout in sorted(matching.items()):
        repo_b = repo.encode()
        for line in stdout.splitlines():
            sys.stdout.buffer.write(
                color.fmtb(repo_b, color.BLUE_B, use_color=use_color) +
                color.fmtb(sep, color.TURQUOISE, use_color=use_color) +
                line + b'\n',
            )
            sys.stdout.buffer.flush()
    return int(not matching)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description='Similar to a distributed `git grep ...`.',
        usage='%(prog)s [options] [GIT_GREP_OPTIONS]',
        add_help=False,
    )
    # Handle --help like normal, pass -h through to git grep
    parser.add_argument(
        '--help', action='help', help='show this help message and exit',
    )
    cli.add_common_args(parser)
    cli.add_repos_with_matches_arg(parser)
    cli.add_repos_without_matches_arg(parser)
    cli.add_output_paths_arg(parser)
    args, rest = parser.parse_known_args(argv)

    config = load_config(args.config_filename)
    if args.repos_with_matches:
        return repos_matching_cli(config, rest)
    elif args.repos_without_matches:
        return repos_not_matching_cli(config, rest)
    else:
        return grep_cli(
            config, rest, output_paths=args.output_paths, use_color=args.color,
        )


if __name__ == '__main__':
    raise SystemExit(main())
