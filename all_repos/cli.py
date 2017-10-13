import multiprocessing
import sys


def add_config_arg(parser):
    parser.add_argument('-C', '--config-filename', default='all-repos.json')


def jobs_type(s):
    jobs = int(s)
    if jobs <= 0:
        return multiprocessing.cpu_count()
    else:
        return jobs


def add_jobs_arg(parser, default=8):
    parser.add_argument('-j', '--jobs', type=jobs_type, default=default)


COLOR_CHOICES = ('auto', 'always', 'never')


def use_color(setting):
    if setting not in COLOR_CHOICES:
        raise ValueError(setting)
    return (
        setting == 'always' or
        (setting == 'auto' and sys.stdout.isatty())
    )


def add_color_arg(parser):
    parser.add_argument(
        '--color', default='auto', type=use_color,
        metavar='{' + ','.join(COLOR_CHOICES) + '}',
        help='Whether to use color in output.  Defaults to `%(default)s`.',
    )


def add_fixer_args(parser):
    add_config_arg(parser)
    add_color_arg(parser)

    mutex = parser.add_mutually_exclusive_group()
    mutex.add_argument('--dry-run', action='store_true')
    mutex.add_argument(
        '-i', '--interactive', action='store_true',
        help='Interactively approve / deny fixes.',
    )
    add_jobs_arg(mutex, default=1)

    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument(
        '--author',
        help=(
            'Override commit author.  '
            'This is passed directly to `git commit`.  '
            "An example: `--author='Herp Derp <herp.derp@umich.edu>'`"
        ),
    )
    parser.add_argument('--repos', nargs='*')
