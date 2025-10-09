from __future__ import annotations

import concurrent.futures
import contextlib
from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Iterable
from typing import ContextManager
from typing import TypeVar

T = TypeVar('T')
T2 = TypeVar('T2')


def exhaust(gen: Iterable[T]) -> None:
    for _ in gen:
        pass


@contextlib.contextmanager
def _in_process() -> Generator[
        Callable[[Callable[[T2], T], Iterable[T2]], Iterable[T]],
]:
    yield map


@contextlib.contextmanager
def _threads(jobs: int) -> Generator[
        Callable[[Callable[[T2], T], Iterable[T2]], Iterable[T]],
]:
    with concurrent.futures.ThreadPoolExecutor(jobs) as ex:
        yield ex.map


def thread_mapper(jobs: int) -> ContextManager[
        Callable[[Callable[[T2], T], Iterable[T2]], Iterable[T]],
]:
    if jobs == 1:
        return _in_process()
    else:
        return _threads(jobs)


@contextlib.contextmanager
def _processes(jobs: int) -> Generator[
        Callable[[Callable[[T2], T], Iterable[T2]], Iterable[T]],
]:
    with concurrent.futures.ProcessPoolExecutor(jobs) as ex:
        yield ex.map


def process_mapper(jobs: int) -> ContextManager[
        Callable[[Callable[[T2], T], Iterable[T2]], Iterable[T]],
]:
    if jobs == 1:
        return _in_process()
    else:
        return _processes(jobs)
