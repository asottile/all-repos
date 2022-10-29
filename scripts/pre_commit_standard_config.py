from __future__ import annotations

import argparse
import io
from typing import Sequence

import yaml

from all_repos import autofix_lib
from all_repos.config import Config

PUPPET = '''\
-   repo: https://github.com/chriskuehl/puppet-pre-commit-hooks
    rev: v2.1.0
    hooks:
    -   id: puppet-lint
        args: [
            --fix, --fail-on-warnings,
            --no-documentation-check,
            --no-arrow_on_right_operand_line-check,
        ]
    -   id: puppet-validate
-   repo: local
    hooks:
    -   id: rubocop
        name: rubocop
        entry: rubocop --auto-correct
        types: [ruby]
        language: ruby
        additional_dependencies: ['rubocop:0.52.0']
'''

CHEETAH = '''\
-   repo: https://github.com/asottile/cheetah_lint
    rev: v1.2.0
    hooks:
    -   id: cheetah-reorder-imports
    -   id: cheetah-flake
'''

ESLINT = '''\
-   repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.11.0
    hooks:
    -   id: eslint
        args: [--fix]
'''

GITHUB_DOT = '''\
-   repo: local
    hooks:
    -   id: no-github-dot-git
        name: No need for .git for github/gitlab urls
        entry: '(github|gitlab).*\\.git'
        files: all-repos.yaml
        language: pygrep
'''

GENERATE_README = '''\
-   repo: local
    hooks:
    -   id: generate-readme
        name: generate readme
        entry: ./generate-readme
        language: python
        additional_dependencies: [pyyaml]
        files: ^(\\.pre-commit-hooks.yaml|generate-readme)$
        pass_filenames: false
    -   id: run-tests
        name: run tests
        entry: pytest tests
        language: python
        additional_dependencies: [pre-commit, pytest]
        always_run: true
        pass_filenames: false
'''

PYTEST = '''\
-   repo: local
    hooks:
    -   id: tests
        name: tests
        entry: pytest tests
        additional_dependencies: [pytest]
        pass_filenames: false
        always_run: true
        language: python
'''

GOFMT = '''\
-   repo: local
    hooks:
    -   id: gofmt
        name: gofmt
        language: system
        entry: gofmt -l -w
        types: [go]
'''

RUBOCOP = '''\
-   repo: local
    hooks:
    -   id: rubocop
        name: rubocop
        entry: rubocop --auto-correct
        types: [ruby]
        language: ruby
        additional_dependencies: ['rubocop:0.63.1']
'''


def find_repos(config: Config) -> set[str]:
    raise NotImplementedError('use --repos')


def apply_fix() -> None:
    with open('.pre-commit-config.yaml') as f:
        orig_contents = f.read()

    try:
        with open('setup.cfg') as f:
            has_setup_cfg = '[metadata]' in f.read()
    except FileNotFoundError:
        has_setup_cfg = False

    has_python = 'flake8' in orig_contents
    has_mypy = 'mirrors-mypy' in orig_contents
    has_puppet = 'puppet-pre-commit-hooks' in orig_contents
    has_cheetah = 'cheetah_lint' in orig_contents
    has_eslint = 'eslint' in orig_contents
    has_github_dot = 'no-github-dot-git' in orig_contents
    has_generate_readme = 'generate-readme' in orig_contents
    has_pytest = 'pytest' in orig_contents
    has_gofmt = 'gofmt' in orig_contents
    has_rubocop = 'rubocop' in orig_contents

    cfg = yaml.load(orig_contents, Loader=yaml.CSafeLoader)

    mypy_deps = []
    for repo in cfg['repos']:
        for hook in repo['hooks']:
            if hook['id'] == 'mypy':
                mypy_deps = hook.get('additional_dependencies', [])

    sio = io.StringIO()

    s = '''\
repos:
-   repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.1.0
    hooks:
    -   id: trailing-whitespace
    -   id: end-of-file-fixer
    -   id: check-yaml
'''
    sio.write(s)

    if has_python:
        s = '''\
    -   id: debug-statements
    -   id: double-quote-string-fixer
    -   id: name-tests-test
    -   id: requirements-txt-fixer
'''
        sio.write(s)

    if has_setup_cfg:
        s = '''\
-   repo: https://github.com/asottile/setup-cfg-fmt
    rev: v1.20.0
    hooks:
    -   id: setup-cfg-fmt
'''
        sio.write(s)

    if has_python:
        s = '''\
-   repo: https://github.com/asottile/reorder_python_imports
    rev: v3.0.1
    hooks:
    -   id: reorder-python-imports
        args: [--py37-plus, --add-import, 'from __future__ import annotations']
-   repo: https://github.com/asottile/add-trailing-comma
    rev: v2.2.1
    hooks:
    -   id: add-trailing-comma
        args: [--py36-plus]
-   repo: https://github.com/asottile/pyupgrade
    rev: v2.31.1
    hooks:
    -   id: pyupgrade
        args: [--py37-plus]
-   repo: https://github.com/pre-commit/mirrors-autopep8
    rev: v1.6.0
    hooks:
    -   id: autopep8
-   repo: https://github.com/PyCQA/flake8
    rev: 4.0.1
    hooks:
    -   id: flake8
'''
        sio.write(s)

    if has_mypy:
        s = '''\
-   repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.942
    hooks:
    -   id: mypy
'''
        sio.write(s)
        if mypy_deps:
            mypy_deps_s = ', '.join(mypy_deps)
            sio.write(f'        additional_dependencies: [{mypy_deps_s}]\n')

    if has_puppet:
        sio.write(PUPPET)
    elif has_rubocop:
        sio.write(RUBOCOP)

    if has_cheetah:
        sio.write(CHEETAH)

    if has_eslint:
        sio.write(ESLINT)

    if has_github_dot:
        sio.write(GITHUB_DOT)

    if has_generate_readme:
        sio.write(GENERATE_README)
    elif has_pytest:
        sio.write(PYTEST)

    if has_gofmt:
        sio.write(GOFMT)

    with open('.pre-commit-config.yaml', 'w') as f:
        f.write(sio.getvalue())

    # This may return nonzero for fixes, that's ok!
    autofix_lib.run('pre-commit', 'run', '--all-files', check=False)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args,
        find_repos=find_repos,
        msg='reorder pre-commit config',
        branch_name='reorder-pre-commit-config',
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
    raise SystemExit(main())
