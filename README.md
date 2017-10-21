[![Build Status](https://travis-ci.org/asottile/all-repos.svg?branch=master)](https://travis-ci.org/asottile/all-repos)
[![Coverage Status](https://coveralls.io/repos/github/asottile/all-repos/badge.svg?branch=master)](https://coveralls.io/github/asottile/all-repos?branch=master)

all-repos
=========

Clone all your repositories and apply sweeping changes.

## Installation

`pip install all-repos`


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
+--- {repo_key4}/
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
+--- {username1}/
    +--- {repo1}.git/
    +--- {repo2}.git/
    +--- {repo3}.git/
+--- {username2}/
    +--- {repo4}.git/
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

#### `push_settings`

There are no configurable settings for `merge_to_master`.

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


## Writing your own push module

First create a module.  This module must have the following api:

### A `Settings` class

This class will receive keyword arguments for all values in the `push_settings`
dictionary.

### `def push(settings: Settings, branch_name: str) -> None:`

This callable will be passed an instance of your `Settings` class.  It should
deploy the branch.  The function will be called with the root of the
repository as the `cwd`.

## Usage

TODO

## Built-in refactoring apis

TODO
