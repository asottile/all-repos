from typing import List


def zsplit(bs: bytes) -> List[bytes]:
    if bs:
        return bs.rstrip(b'\0').split(b'\0')
    else:
        return []
