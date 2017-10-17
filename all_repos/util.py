def zsplit(bs):
    if bs:
        return bs.rstrip(b'\0').split(b'\0')
    else:
        return []
