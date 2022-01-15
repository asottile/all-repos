from __future__ import annotations

import io


def urlopen_side_effect(url_mapping):
    def urlopen(request):
        return url_mapping[request.get_full_url()]
    return urlopen


class FakeResponse(io.BytesIO):
    def __init__(self, body, *, next_link=None):
        super().__init__(body)
        link = None if next_link is None else f'<{next_link}>; rel="next"'
        self.headers = {'link': link}
