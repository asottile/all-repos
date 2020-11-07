import base64
from typing import Dict
from typing import NamedTuple

from all_repos import bitbucket_api
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    username: str
    app_password: str

    @property
    def auth(self) -> str:
        value = f'{self.username}:{self.app_password}'
        return base64.b64encode(value.encode()).decode()

    # TODO: https://github.com/python/mypy/issues/8543
    def __repr__(self) -> str:
        return hide_api_key_repr(self, key='app_password')


def list_repos(settings: Settings) -> Dict[str, str]:
    repos = bitbucket_api.get_all(
        'https://api.bitbucket.org/2.0/repositories?pagelen=100&role=member',
        headers={'Authorization': f'Basic {settings.auth}'},
    )

    return {
        repo['full_name']: 'git@bitbucket.org:{}.git'.format(repo['full_name'])
        for repo in repos
    }
