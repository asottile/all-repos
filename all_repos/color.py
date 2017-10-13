BLUE_B = '\033[1;34m'
RED = '\033[31m'
RED_H = '\033[41m'
TURQUOISE = '\033[36m'
TURQUOISE_H = '\033[46;30m'
NORMAL = '\033[m'


def fmt(text, color, *, use_color):
    if use_color:
        return f'{color}{text}{NORMAL}'
    else:
        return text


def fmtb(bs, color, *, use_color):
    if use_color:
        return b'%s%s%s' % (color.encode(), bs, NORMAL.encode())
    else:
        return bs
