import base64
from typing import Dict
from typing import NamedTuple

from all_repos import bitbucket_api


class Settings(NamedTuple):
    username: str
    app_password: str

    def b64_encode_username_password(self) -> str:
        value = f'{self.username}:{self.app_password}'
        return base64.b64encode(bytes(value, 'utf-8')).decode('ascii')


def list_repos(settings: Settings) -> Dict[str, str]:
    repos = bitbucket_api.get_all(
        'https://api.bitbucket.org/2.0/repositories?pagelen=100&role=member',  # noqa: E501,E261
        headers={'Authorization': f'Basic {settings.b64_encode_username_password()}'},  # noqa: E501,E261
    )

    return {
        repo['full_name']: 'git@bitbucket.org:{}.git'.format(repo['full_name'])
        for repo in repos
    }
