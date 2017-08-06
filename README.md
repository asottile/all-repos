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
    "mod": "all_repos.sources.github",
    "settings":  {
        "api_key": "...",
        "username": "asottile"
    }
}
```

- `output_dir`: where repositories will be cloned to when `all-repos-clone` is
  run.
- `mod`: the module import path to a `source`, see below for builtin
  sources as well as directions for writing your own.
- `settings`: the source-type-specific settings, the source's
  documentation will explain the various possible values here.
- `include` (default `""`): python regex for selecting repositories.  Only
  repository names which match this regex will be included.
- `exclude` (default `"^$"`): python regex for excluding repositories.
  Repository names which match this regex will be excluded.

## Sources

### `all_repos.sources.json_file`

Clones all repositories listed in a file.  The file must be formatted as
follows:

```json
{
    "example/repo1": "https://git.example.com/example/repo1",
    "repo2": "https://git.example.com/repo2"
}
```

#### Required `settings`

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

### `all_repos.sources.github`

Clones all repositories available to a user on github.

#### Required `settings`

- `api_key`: the api key which the user will log in as.
    - Use [the settings tab](//github.com/settings/tokens/new) to create a
      personal access token.
    - The minimum scope required to function is `public_repo`, though you'll
      need `repo` to access private repositories.
- `username`: the github username you will log in as.

#### Optional `settings`

- `collaborator` (default `false`): whether to include repositories which are
  not owned but can be contributed to as a collaborator.
- `forks` (default `false`): whether to include repositories which are forks.
- `private` (default `false`): whether to include private repositories.

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

To create a `source`, first create a module.  This module must have the
following api:

### A `Settings` class

This class will receive keyword arguments for all values in the `settings`
dictionary.

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


## Usage

TODO

## Built-in refactoring apis

TODO
