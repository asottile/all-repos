import argparse
import configparser
import io
import os.path
import sys
from typing import Dict
from typing import Optional
from typing import Sequence
from typing import Set
from typing import Tuple

from all_repos import autofix_lib
from all_repos.config import Config
from all_repos.grep import repos_matching

KEYS_ORDER: Tuple[Tuple[str, Tuple[str, ...]], ...] = (
    (
        'metadata', (
            'name', 'version', 'description',
            'long_description', 'long_description_content_type',
            'url', 'author', 'author_email', 'license', 'license_file',
            'platforms', 'classifiers',
        ),
    ),
    (
        'options', (
            'packages', 'py_modules', 'install_requires', 'python_requires',
        ),
    ),
    ('options.sections.find', ('where', 'exclude', 'include')),
    ('options.entry_points', ('console_scripts',)),
    ('options.extras_require', ()),
    ('options.package_data', ()),
    ('options.exclude_package_data', ()),
)


def find_repos(config: Config) -> Set[str]:
    return repos_matching(config, ('=', '--', 'setup.py'))


def apply_fix() -> None:
    autofix_lib.run(sys.executable, '-m', 'setup_py_upgrade', '.')

    cfg = configparser.ConfigParser()
    cfg.read('setup.cfg')

    # normalize names to underscores so sdist / wheel have the same prefix
    cfg['metadata']['name'] = cfg['metadata']['name'].replace('-', '_')

    # if README.md exists, set `long_description` + content type
    if os.path.exists('README.md'):
        cfg['metadata']['long_description'] = 'file: README.md'
        cfg['metadata']['long_description_content_type'] = 'text/markdown'

    if os.path.exists('LICENSE'):
        cfg['metadata']['license_file'] = 'LICENSE'

        with open('LICENSE') as f:
            contents = f.read()

        # TODO: pick a better way to identify licenses
        if 'Permission is hereby granted, free of charge, to any' in contents:
            cfg['metadata']['license'] = 'MIT'
            cfg['metadata']['classifiers'] = (
                cfg['metadata'].get('classifiers', '').rstrip() +
                '\nLicense :: OSI Approved :: MIT License'
            )

    # TODO:
    # add the necessary python classifiers
    # `python_requires`

    if 'classifiers' in cfg['metadata']:
        classifiers = sorted(set(cfg['metadata']['classifiers'].split('\n')))
        cfg['metadata']['classifiers'] = '\n'.join(classifiers)

    sections: Dict[str, Dict[str, str]] = {}
    for section, key_order in KEYS_ORDER:
        if section not in cfg:
            continue

        new_section = {
            k: cfg[section].pop(k) for k in key_order if k in cfg[section]
        }
        # sort any remaining keys
        new_section.update(sorted(cfg[section].items()))

        sections[section] = new_section
        cfg.pop(section)

    for section in cfg.sections():
        sections[section] = dict(cfg[section])
        cfg.pop(section)

    for k, v in sections.items():
        cfg[k] = v

    sio = io.StringIO()
    cfg.write(sio)
    with open('setup.cfg', 'w') as f:
        contents = sio.getvalue().strip() + '\n'
        contents = contents.replace('\t', '    ')
        contents = contents.replace(' \n', '\n')
        f.write(contents)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    autofix_lib.assert_importable(
        'setup_py_upgrade', install='setup-py-upgrade',
    )

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='Migrate setup.py to setup.cfg declarative metadata',
        branch_name='setup-py-upgrade',
    )

    autofix_lib.fix(
        repos,
        apply_fix=apply_fix,
        config=config,
        commit=commit,
        autofix_settings=autofix_settings,
    )
    return 0


if __name__ == '__main__':
    exit(main())
