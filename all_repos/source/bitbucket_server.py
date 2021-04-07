import base64
from typing import Dict
from typing import NamedTuple
from typing import Optional

from all_repos import bitbucket_server_api
from all_repos.util import hide_api_key_repr


class Settings(NamedTuple):
    username: str
    app_password: str
    base_url: str
    project: Optional[str] = None

    @property
    def auth(self) -> str:
        value = f'{self.username}:{self.app_password}'
        return base64.b64encode(value.encode()).decode()

    def __repr__(self) -> str:
        return hide_api_key_repr(self, key='app_password')


def list_repos(settings: Settings) -> Dict[str, str]:
    if settings.project:
        end_point = f'rest/api/1.0/projects/{settings.project}/repos'
    else:
        end_point = 'rest/api/1.0/repos'

    base_url = settings.base_url
    repos = bitbucket_server_api.get_all(
        f'https://{base_url}/{end_point}?limit=100&permission=REPO_READ',
        headers={'Authorization': f'Basic {settings.auth}'},
    )

    return {
        f'{repo["project"]["key"]}/{repo["slug"]}': origin['href']
        for repo in repos
        for origin in repo['links']['clone']
        if origin['name'] == 'ssh'
    }
