from __future__ import annotations


n_conftest_threads = 3

# a conftest that runs tests in a threadpool. You can think of this as "like pytest-xdist,
# but using threads instead of processes". This is a nice conftest for flushing out
# concurrency bugs in pytest itself.
threaded_conftest = f"""
import sys
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor

# make thread switches more common
sys.setswitchinterval(0.000001)
n = {n_conftest_threads}

def pytest_runtestloop(session):
    queue = Queue()
    for item in session.items:
        queue.put(item)

    def worker(n):
        threading.current_thread().name = f"pytest-thread-{{n}}"
        try:
            item = queue.get_nowait()
        except Empty:
            return

        while item is not None:
            try:
                next_item = queue.get_nowait()
            except Empty:
                next_item = None

            item.config.hook.pytest_runtest_protocol(
                item=item, nextitem=next_item
            )
            item = next_item

    with ThreadPoolExecutor(max_workers=n) as executor:
        futures = [executor.submit(worker, n=i) for i in range(n)]
        for future in futures:
            future.result()
    return True
"""
