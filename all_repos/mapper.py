import concurrent.futures
import contextlib
from typing import Any
from typing import Callable
from typing import ContextManager
from typing import Generator
from typing import Iterable
from typing import TypeVar


T = TypeVar('T')
MapCallable = Callable[[Callable[..., T], Iterable[Any]], Iterable[T]]


def exhaust(gen: Iterable) -> None:
    for _ in gen:
        pass


@contextlib.contextmanager
def _in_process() -> Generator[MapCallable, None, None]:
    yield map


@contextlib.contextmanager
def _threads(jobs: int) -> Generator[MapCallable, None, None]:
    with concurrent.futures.ThreadPoolExecutor(jobs) as ex:
        yield ex.map


def thread_mapper(jobs: int) -> ContextManager[MapCallable]:
    if jobs == 1:
        return _in_process()
    else:
        return _threads(jobs)


@contextlib.contextmanager
def _processes(jobs: int) -> Generator[MapCallable, None, None]:
    with concurrent.futures.ProcessPoolExecutor(jobs) as ex:
        yield ex.map


def process_mapper(jobs: int) -> ContextManager[MapCallable]:
    if jobs == 1:
        return _in_process()
    else:
        return _processes(jobs)
