import argparse
import multiprocessing
import os
import sys
from typing import Union


ParserType = Union[argparse.ArgumentParser, argparse._MutuallyExclusiveGroup]


def jobs_type(s: str) -> int:
    jobs = int(s)
    if jobs <= 0:
        return multiprocessing.cpu_count()
    else:
        return jobs


def add_jobs_arg(parser: ParserType, default: int = 8) -> None:
    parser.add_argument(
        '-j', '--jobs', type=jobs_type, default=default,
        help=(
            'how many concurrent jobs will be used to complete the '
            'operation.  Specify 0 or -1 to match the number of cpus '
            '(default `%(default)s`).'
        ),
    )


COLOR_CHOICES = ('auto', 'always', 'never')


def use_color(setting: str) -> bool:
    if setting not in COLOR_CHOICES:
        raise ValueError(setting)
    return (
        setting == 'always' or
        (setting == 'auto' and sys.stdout.isatty())
    )


def add_common_args(parser: ParserType) -> None:
    parser.add_argument(
        '-C', '--config-filename',
        default=os.getenv('ALL_REPOS_CONFIG_FILENAME') or 'all-repos.json',
        help='use a non-default config file (default `%(default)s`).',
    )
    parser.add_argument(
        '--color', default='auto', type=use_color,
        metavar='{' + ','.join(COLOR_CHOICES) + '}',
        help='use color in output (default `%(default)s`).',
    )


def add_repos_with_matches_arg(parser: ParserType) -> None:
    parser.add_argument(
        '--repos-with-matches', action='store_true',
        help='only print repositories with matches.',
    )


def add_output_paths_arg(parser: ParserType) -> None:
    parser.add_argument(
        '--output-paths', action='store_true',
        help=(
            f'Use `{os.sep}` as a separator instead of `:` in outputs (often '
            f'helpful for scripting).'
        ),
    )
