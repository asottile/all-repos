from __future__ import annotations

import pytest

from all_repos import mapper


def square(n):
    return n * n


@pytest.mark.parametrize(
    'ctx',
    (
        mapper.process_mapper(1),
        mapper.process_mapper(2),
        mapper.thread_mapper(1),
        mapper.thread_mapper(2),
    ),
)
def test_mappers(ctx):
    with ctx as do_map:
        assert tuple(do_map(square, (3, 4, 5))) == (9, 16, 25)


def test_exhaust():
    def gen():
        yield 1
        yield 2
        yield 3

    inst = gen()
    assert next(inst) == 1
    mapper.exhaust(inst)
    with pytest.raises(StopIteration):
        next(inst)
