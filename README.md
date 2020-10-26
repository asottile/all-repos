[![Build Status](https://dev.azure.com/asottile/asottile/_apis/build/status/asottile.all-repos?branchName=master)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=33&branchName=master)
[![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/asottile/asottile/33/master.svg)](https://dev.azure.com/asottile/asottile/_build/latest?definitionId=33&branchName=master)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/asottile/all-repos/master.svg)](https://results.pre-commit.ci/latest/github/asottile/all-repos/master)

all-repos
=========

Clone all your repositories and apply sweeping changes.

## Installation

`pip install all-repos`


## CLI

All command line interfaces provided by `all-repos` provide the following
options:

- `-h` / `--help`: show usage information
- `-C CONFIG_FILENAME` / `--config-filename CONFIG_FILENAME`: use a non-default
  config file (the default `all-repos.json` can be changed with the environment
  variable `ALL_REPOS_CONFIG_FILENAME`).
- `--color {auto,always,never}`: use color in output (default `auto`).


### `all-repos-complete [options]`

Add `git clone` tab completion for all-repos repositories.

Requires [jq](https://stedolan.github.io/jq/) to function.

Add to `.bash_profile`:

```bash
eval "$(all-repos-complete -C ~/.../all-repos.json --bash)"
```

### `all-repos-clone [options]`

Clone all the repositories into the `output_dir`.  If run again, this command
will update existing repositories.

Options:

- `-j JOBS` / `--jobs JOBS`: how many concurrent jobs will be used to complete
  the operation.  Specify 0 or -1 to match the number of cpus.  (default `8`).

Sample invocations:

- `all-repos-clone`: clone the repositories specified in `all-repos.json`
- `all-repos-clone -C all-repos2.json`: clone using a non-default config
  filename.

### `all-repos-find-files [options] PATTERN`

Similar to a distributed `git ls-files | grep -P PATTERN`.

Arguments:
- `PATTERN`: the [python regex](https://docs.python.org/3/library/re.html)
  to match.

Options:

- `--repos-with-matches`: only print repositories with matches.

Sample invocations:

- `all-repos-find-files setup.py`: find all `setup.py` files.
- `all-repos-find-files --repos setup.py`: find all repositories containing
  a `setup.py`.

### `all-repos-grep [options] [GIT_GREP_OPTIONS]`

Similar to a distributed `git grep ...`.

Options:

- `--repos-with-matches`: only print repositories with matches.
- `GIT_GREP_OPTIONS`: additional arguments will be passed on to `git grep`.
  see `git grep --help` for available options.

Sample invocations:

- `all-repos-grep pre-commit -- 'requirements*.txt'`: find all repositories
  which have `pre-commit` listed in a requirements file.
- `all-repos-grep -L six -- setup.py`: find setup.py files which do not
  contain `six`.

### `all-repos-list-repos [options]`

List all cloned repository names.

### `all-repos-manual [options]`

Interactively apply a manual change across repos.

_note_: `all-repos-manual` will always run in `--interactive` autofixing mode.

_note_: `all-repos-manual` _requires_ the `--repos` autofixer option.

Options:

- [autofix options](#all_reposautofix_libadd_fixer_args): `all-repos-manual` is
  an autofixer and supports all of the autofixer options.
- `--branch-name BRANCH_NAME`: override the autofixer branch name (default
  `all-repos-manual`).
- `--commit-msg COMMIT_MSG` (required): set the autofixer commit message.


### `all-repos-sed [options] EXPRESSION FILENAMES`

Similar to a distributed
`git ls-files -z -- FILENAMES | xargs -0 sed -i EXPRESSION`.

_note_: this assumes GNU sed. If you're on macOS, install `gnu-sed` with Homebrew:

```bash
brew install gnu-sed

# Add to .bashrc / .zshrc
export PATH="/usr/local/opt/gnu-sed/libexec/gnubin:$PATH"
```

Arguments:

- `EXPRESSION`: sed program. For example: `s/hi/hello/g`.
- `FILENAMES`: filenames glob (passed to `git ls-files`).

Options:

- [autofix options](#all_reposautofix_libadd_fixer_args): `all-repos-sed` is
  an autofixer and supports all of the autofixer options.
- `-r` / `--regexp-extended`: use extended regular expressions in the script.
  See `man sed` for further details.
- `--branch-name BRANCH_NAME` override the autofixer branch name (default
  `all-repos-sed`).
- `--commit-msg COMMIT_MSG` override the autofixer commit message.  (default
  `git ls-files -z -- FILENAMES | xargs -0 sed -i ... EXPRESSION`).

Sample invocations:

- `all-repos-sed 's/foo/bar/g' -- '*'`: replace `foo` with `bar` in all files.

## Configuring

A configuration file looks roughly like this:

```json
{
    "output_dir": "output",
    "source": "all_repos.source.github",
    "source_settings":  {
        "api_key": "...",
        "username": "asottile"
    },
    "push": "all_repos.push.github_pull_request",
    "push_settings": {
        "api_key": "...",
        "username": "asottile"
    }
}
```

- `output_dir`: where repositories will be cloned to when `all-repos-clone` is
  run.
- `source`: the module import path to a `source`, see below for builtin
  source modules as well as directions for writing your own.
- `source_settings`: the source-type-specific settings, the source module's
  documentation will explain the various possible values.
- `push`: the module import path to a `push`, see below for builtin push
  modules as well as directions for writing your own.
- `push_settings`: the push-type-specific settings, the push module's
  documentation will explain the various possible values.
- `include` (default `""`): python regex for selecting repositories.  Only
  repository names which match this regex will be included.
- `exclude` (default `"^$"`): python regex for excluding repositories.
  Repository names which match this regex will be excluded.
- `all_branches` (default `false`): whether to clone all of the branches or
  just the default upstream branch.

## Source modules

### `all_repos.source.json_file`

Clones all repositories listed in a file.  The file must be formatted as
follows:

```json
{
    "example/repo1": "https://git.example.com/example/repo1",
    "repo2": "https://git.example.com/repo2"
}
```

#### Required `source_settings`

- `filename`: file containing repositories one-per-line.

#### Directory location

```
output/
+--- repos.json
+--- repos_filtered.json
+--- {repo_key1}/
+--- {repo_key2}/
+--- {repo_key3}/
```

### `all_repos.source.github`

Clones all repositories available to a user on github.

#### Required `source_settings`

- `api_key`: the api key which the user will log in as.
    - Use [the settings tab](//github.com/settings/tokens/new) to create a
      personal access token.
    - The minimum scope required to function is `public_repo`, though you'll
      need `repo` to access private repositories.
- `username`: the github username you will log in as.

#### Optional `source_settings`

- `collaborator` (default `false`): whether to include repositories which are
  not owned but can be contributed to as a collaborator.
- `forks` (default `false`): whether to include repositories which are forks.
- `private` (default `false`): whether to include private repositories.
- `archived` (default: `false`): whether to include archived repositories.
- `base_url` (default: `https://api.github.com`) is the base URL to the Github
  API to use (for Github Enterprise support set this to `https://{your_domain}/api/v3`).

#### Directory location

```
output/
+--- repos.json
+--- repos_filtered.json
+--- {username1}/
    +--- {repo1}/
    +--- {repo2}/
+--- {username2}/
    +--- {repo3}/
```

### `all_repos.source.github_forks`

Clones all repositories forked from a repository on github.

#### Required `source_settings`

- `api_key`: the api key which the user will log in as.
    - Use [the settings tab](//github.com/settings/tokens/new) to create a
      personal access token.
    - The minimum scope required to function is `public_repo`.
- `repo`: the repo which has forks

#### Optional `source_settings`

- `collaborator` (default `true`): whether to include repositories which are
  not owned but can be contributed to as a collaborator.
- `forks` (default `true`): whether to include repositories which are forks.
- `private` (default `false`): whether to include private repositories.
- `archived` (default: `false`): whether to include archived repositories.
- `base_url` (default: `https://api.github.com`) is the base URL to the Github
  API to use (for Github Enterprise support set this to `https://{your_domain}/api/v3`).

#### Directory location

See the directory structure for
[`all_repos.source.github`](#all_repossourcegithub).


### `all_repos.source.github_org`

Clones all repositories from an organization on github.

#### Required `source_settings`

- `api_key`: the api key which the user will log in as.
    - Use [the settings tab](//github.com/settings/tokens/new) to create a
      personal access token.
    - The minimum scope required to function is `public_repo`, though you'll
      need `repo` to access private repositories.
- `org`: the organization to clone from

#### Optional `source_settings`

- `collaborator` (default `true`): whether to include repositories which are
  not owned but can be contributed to as a collaborator.
- `forks` (default `false`): whether to include repositories which are forks.
- `private` (default `false`): whether to include private repositories.
- `archived` (default: `false`): whether to include archived repositories.
- `base_url` (default: `https://api.github.com`) is the base URL to the Github
  API to use (for Github Enterprise support set this to `https://{your_domain}/api/v3`).

#### Directory location

See the directory structure for
[`all_repos.source.github`](#all_repossourcegithub).

### `all_repos.source.gitolite`

Clones all repositories available to a user on a
[gitolite](http://gitolite.com/gitolite/index.html) host.

#### Required `source_settings`

- `username`: the user to SSH to the server as (usually `git`)
- `hostname`: the hostname of your gitolite server (e.g. `git.mycompany.com`)

The gitolite API is served over SSH.  It is assumed that when `all-repos-clone`
is called, it's possible to make SSH connections with the username and hostname
configured here in order to query that API.

#### Optional `source_settings`

- `mirror_path` (default `None`): an optional mirror to clone repositories from.
  This is a Python format string, and can use the variable `repo_name`.

  This can be anything git understands, such as another remote server (e.g.
  `gitmirror.mycompany.com:{repo_name}`) or a local path (e.g.
  `/gitolite/git/{repo_name}.git`).

#### Directory location

```
output/
+--- repos.json
+--- repos_filtered.json
+--- {repo_name1}.git/
+--- {repo_name2}.git/
+--- {repo_name3}.git/
```


### `all_repos.source.bitbucket`

Clones all repositories available to a user on Bitbucket.

#### Required `source_settings`

- `username`: the Bitbucket username you will log in as.
- `app_password`: the authentication method for the above user to login with
    - Create an application password within your [account settings](https://bitbucket.org/account/admin/app-passwords).
    - We need the scope: Repositories -> Read

#### Directory location

```
output/
+--- repos.json
+--- repos_filtered.json
+--- {username1}/
    +--- {repo1}/
    +--- {repo2}/
+--- {username2}/
    +--- {repo3}/
```

## Writing your own source

First create a module.  This module must have the following api:

### A `Settings` class

This class will receive keyword arguments for all values in the
`source_settings` dictionary.

An easy way to implement the `Settings` class is by using a `namedtuple`:

```python
Settings = collections.namedtuple('Settings', ('required_thing', 'optional'))
Settings.__new__.__defaults__ = ('optional default value',)
```

In this example, the `required_thing` setting is a **required** setting
whereas `optional` may be omitted (and will get a default value of
`'optional default value'`).

### `def list_repos(settings: Settings) -> Dict[str, str]:` callable

This callable will be passed an instance of your `Settings` class.  It must
return a mapping from `{repo_name: repository_url}`.  The `repo_name` is the
directory name inside the `output_dir`.

## Push modules

### `all_repos.push.merge_to_master`

Merges the branch directly to `master` and pushes.  The commands it runs look
roughly like this:

```bash
git checkout master
git pull
git merge --no-ff $BRANCH
git push origin HEAD
```

#### Optional `push_settings`

- `fast_forward` (default: `false`): if `true`, perform a fast-forward
    merge (`--ff-only`). If `false`, create a merge commit (`--no-ff`).

### `all_repos.push.github_pull_request`

Pushes the branch to `origin` and then creates a github pull request for the
branch.

#### Required `push_settings`

- `api_key`: the api key which the user will log in as.
    - Use [the settings tab](//github.com/settings/tokens/new) to create a
      personal access token.
    - The minimum scope required to function is `public_repo`, though you'll
      need `repo` to access private repositories.
- `username`: the github username you will log in as.

#### Optional `push_settings`

- `fork` (default: `false`): (if applicable) a fork will be created and pushed
  to instead of the upstream repository.  The pull request will then be made
  to the upstream repository.
- `base_url` (default: `https://api.github.com`) is the base URL to the Github
  API to use (for Github Enterprise support set this to `https://{your_domain}/api/v3`).

### `all_repos.push.readonly`

Does nothing.

#### `push_settings`

There are no configurable settings for `readonly`.

## Writing your own push module

First create a module.  This module must have the following api:

### A `Settings` class

This class will receive keyword arguments for all values in the `push_settings`
dictionary.

### `def push(settings: Settings, branch_name: str) -> None:`

This callable will be passed an instance of your `Settings` class.  It should
deploy the branch.  The function will be called with the root of the
repository as the `cwd`.

## Writing an autofixer

An autofixer applies a change over all repositories.

`all-repos` provides several api functions to write your autofixers with:

### `all_repos.autofix_lib.add_fixer_args`

```python
def add_fixer_args(parser):
```

Adds the autofixer cli options.

Options:

- `--dry-run`: show what would happen but do not push.
- `-i` / `--interactive`: interactively approve / deny fixes.
- `-j JOBS` / `--jobs JOBS`: how many concurrent jobs will be used to complete
  the operation.  Specify 0 or -1 to match the number of cpus.  (default `1`).
- `--limit LIMIT`: maximum number of repos to process (default: unlimited).
- `--author AUTHOR`: override commit author.  This is passed directly to
  `git commit`.  An example: `--author='Herp Derp <herp.derp@umich.edu>'`.
- `--repos [REPOS [REPOS ...]]`: run against specific repositories instead.
  This is especially useful with `xargs autofixer ... --repos`.  This can be
  used to specify repositories which are not managed by `all-repos`.

### `all_repos.autofix_lib.from_cli`

```python
def from_cli(args, *, find_repos, msg, branch_name):
```

Parse cli arguments and produce `autofix_lib` primitives.  Returns
`(repos, config, commit, autofix_settings)`.  This is handled separately from
`fix` to allow for fixers to adjust arguments.

- `find_repos`: callback taking `Config` as a positional argument.
- `msg`: commit message.
- `branch_name`: identifier used to construct the branch name.

###  `all_repos.autofix_lib.fix`

```python
def fix(
        repos, *,
        apply_fix,
        check_fix=_noop_check_fix,
        config: Config,
        commit: Commit,
        autofix_settings: AutofixSettings,
):
```

Apply the fix.

- `apply_fix`: callback which will be called once per repository.  The `cwd`
  when the function is called will be the root of the repository.


### `all_repos.autofix_lib.run`

```python
def run(*cmd, **kwargs):
```

Wrapper around `subprocess.run` which prints the command it will run.  Unlike
`subprocess.run`, this defaults `check=True` unless explicitly disabled.

### Example autofixer

The trivial autofixer is as follows:

```python
import argparse

from all_repos import autofix_lib

def find_repos(config):
    return []

def apply_fix():
    pass

def main(argv=None):
    parser = argparse.ArgumentParser()
    autofix_lib.add_fixer_args(parser)
    args = parser.parse_args(argv)

    repos, config, commit, autofix_settings = autofix_lib.from_cli(
        args, find_repos=find_repos, msg='msg', branch_name='branch-name',
    )
    autofix_lib.fix(
        repos, apply_fix=apply_fix, config=config, commit=commit,
        autofix_settings=autofix_settings,
    )

if __name__ == '__main__':
    exit(main())
```

You can find some more involved examples in [all_repos/autofix](https://github.com/asottile/all-repos/tree/master/all_repos/autofix):
- `all_repos.autofix.azure_pipelines_autoupdate`: upgrade pinned azure
  pipelines template repository references.
- `all_repos.autofix.pre_commit_autoupdate`: runs `pre-commit autoupdate`.
- `all_repos.autofix.pre_commit_autopep8_migrate`: migrates `autopep8-wrapper`
  from [pre-commit/pre-commit-hooks] to [mirrors-autopep8].
- `all_repos.autofix.pre_commit_cache_dir`: updates the cache directory
  for travis-ci / appveyor for pre-commit 1.x.
- `all_repos.autofix.pre_commit_flake8_migrate`: migrates `flake8` from
  [pre-commit/pre-commit-hooks] to [pycqa/flake8].
- `all_repos.autofix.pre_commit_migrate_config`: runs
  `pre-commit migrate-config`.
- `all_repos.autofix.setup_py_upgrade`: runs [setup-py-upgrade] and then
  [setup-cfg-fmt] to migrate `setup.py` to `setup.cfg`.

[pre-commit/pre-commit-hooks]: https://github.com/pre-commit/pre-commit-hooks
[mirrors-autopep8]: https://github.com/pre-commit/mirrors-autopep8
[pycqa/flake8]: https://gitlab.com/pycqa/flake8
[setup-py-upgrade]: https://github.com/asottile/setup-py-upgrade
[setup-cfg-fmt]: https://github.com/asottile/setup-cfg-fmt
