import pytest

from all_repos.util import zsplit


@pytest.mark.parametrize(
    ('bs', 'expected'),
    (
        (b'', []),
        (b'\0', [b'']),
        (b'a\0b\0', [b'a', b'b']),
    ),
)
def test_zsplit(bs, expected):
    assert zsplit(bs) == expected
