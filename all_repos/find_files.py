import argparse
import os.path
import re
import subprocess
import sys
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Tuple

from all_repos import cli
from all_repos import color
from all_repos.config import Config
from all_repos.config import load_config
from all_repos.util import zsplit


def ls_files(config: Config, repo: str) -> Tuple[str, List[bytes]]:
    path = os.path.join(config.output_dir, repo)
    ret = subprocess.run(
        ('git', '-C', path, 'ls-files', '-z'),
        stdout=subprocess.PIPE, check=True,
    )
    return path, zsplit(ret.stdout)


def find_files(config: Config, pattern: str) -> Dict[str, List[bytes]]:
    regex = re.compile(pattern.encode())
    repos = config.get_cloned_repos()
    ret = {}
    for repo in repos:
        repo, filenames = ls_files(config, repo)
        matched = [f for f in filenames if regex.search(f)]
        if matched:
            ret[repo] = matched
    return ret


def find_files_repos_cli(
        config: Config, pattern: str,
        *,
        use_color: bool,
) -> int:
    repo_files = find_files(config, pattern)
    for repo in repo_files:
        print(repo)
    return not repo_files


def find_files_cli(
        config: Config,
        pattern: str,
        *,
        output_paths: bool,
        use_color: bool,
) -> int:
    sep = os.sep.encode() if output_paths else b':'
    repo_files = find_files(config, pattern)
    for repo, matching in repo_files.items():
        for filename in matching:
            sys.stdout.buffer.write(
                color.fmtb(repo.encode(), color.BLUE_B, use_color=use_color) +
                color.fmtb(sep, color.TURQUOISE, use_color=use_color) +
                filename + b'\n',
            )
    return not repo_files


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            'Similar to a distributed `git ls-files | grep -P PATTERN`.'
        ),
        usage='%(prog)s [options] PATTERN',
    )
    cli.add_common_args(parser)
    cli.add_repos_with_matches_arg(parser)
    cli.add_output_paths_arg(parser)
    parser.add_argument('pattern', help='the python regex to match.')
    args = parser.parse_args(argv)

    config = load_config(args.config_filename)
    if args.repos_with_matches:
        return find_files_repos_cli(config, args.pattern, use_color=args.color)
    else:
        return find_files_cli(
            config, args.pattern,
            output_paths=args.output_paths, use_color=args.color,
        )


if __name__ == '__main__':
    exit(main())
