from typing import Any
from typing import Dict
from typing import List
from typing import TypeVar


def _strip_trailing_dot_git(ssh_url: str) -> str:
    if ssh_url.endswith('.git'):
        return ssh_url[:-1 * len('.git')]
    else:
        return ssh_url


def filter_repos(
        repos: List[Dict[str, Any]], *,
        forks: bool, private: bool, collaborator: bool, archived: bool,
) -> Dict[str, str]:
    return {
        repo['full_name']: _strip_trailing_dot_git(repo['ssh_url'])
        for repo in repos
        if (
            (forks or not repo['fork']) and
            (private or not repo['private']) and
            (collaborator or repo['permissions']['admin']) and
            (archived or not repo['archived'])
        )
    }


T = TypeVar('T', List[Any], Dict[str, Any], Any)


def better_repr(obj: T) -> T:
    if isinstance(obj, list):
        return [better_repr(o) for o in obj]
    elif isinstance(obj, dict):
        return {
            k: better_repr(v) for k, v in obj.items() if not k.endswith('url')
        }
    else:
        return obj
