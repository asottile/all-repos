import concurrent.futures
import contextlib


def exhaust(gen):
    for _ in gen:
        pass


@contextlib.contextmanager
def _in_process():
    yield map


@contextlib.contextmanager
def _threads(jobs):
    with concurrent.futures.ThreadPoolExecutor(jobs) as ex:
        yield ex.map


def thread_mapper(jobs):
    if jobs == 1:
        return _in_process()
    else:
        return _threads(jobs)


@contextlib.contextmanager
def _processes(jobs):
    with concurrent.futures.ProcessPoolExecutor(jobs) as ex:
        yield ex.map


def process_mapper(jobs):
    if jobs == 1:
        return _in_process()
    else:
        return _processes(jobs)
