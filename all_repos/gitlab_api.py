from typing import Any
from typing import Dict
from typing import List


def filter_repos_from_settings(
    repos: List[Dict[str, Any]], settings: Any,
) -> Dict[str, str]:
    return filter_repos(
        repos,
        archived=settings.archived,
    )


def filter_repos(
        repos: List[Dict[str, Any]], *,
        archived: bool,
) -> Dict[str, str]:
    return {
        repo['path_with_namespace']: repo['ssh_url_to_repo']
        for repo in repos
        if (
            archived or not repo['archived']
        )
    }
