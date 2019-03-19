import argparse
import os
from typing import Optional
from typing import Sequence

from all_repos import cli
from all_repos.config import load_config


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description='List all cloned repository names.',
        usage='all-repos-list-repos [options]',
    )
    cli.add_common_args(parser)
    cli.add_output_paths_arg(parser)
    args = parser.parse_args(argv)

    config = load_config(args.config_filename)
    for repo in config.get_cloned_repos():
        if args.output_paths:
            print(os.path.join(config.output_dir, repo))
        else:
            print(repo)
    return 0


if __name__ == '__main__':
    exit(main())
