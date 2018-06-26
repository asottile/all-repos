import io


def urlopen_side_effect(url_mapping):
    def urlopen(request):
        return url_mapping[request.get_full_url()]
    return urlopen


class FakeResponse(io.BytesIO):
    def __init__(self, body, *, next_link=None):
        super().__init__(body)
        if next_link is None:
            self.headers = {'link': None}
        else:
            self.headers = {'link': f'<{next_link}>; rel="next"'}
