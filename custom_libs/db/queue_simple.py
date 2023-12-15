"""
Queue manager to be used in db-interaction modules
It can be called from different threads
It accepts many tasks and processes them one by one
in one thread in order they were placed
and returns result of each task
It uses threading.Lock() to obtain thread-safe behavior
Common usage:
    # put a task
    query_id = queue_simple.add(fn, fnArg1, ..., fnArgN)
    # loop to get result
    while True:
        if not queue_simple.ready(query_id):
            time.sleep(0.05)
            continue
        # get the result
        return queue_simple.get(query_id)

Note: you shouldn't create db connection for each db query
or most probably the app will crash
Instead of it, you should use already established db connection
in your db module (implemented now by default)

In the end of the main script you should call
queue_simple.wait_finishing()
to stop global queue loop and release the thread or the app will hang
"""

import threading
import time
import uuid
from collections import deque
from typing import Callable, Dict, Optional, Sequence

from custom_libs.log import log

__version__ = '2.0.0'
__changelog__ = """
2.0.0
auto-starting thread only after the 1st call to add()
1.3.0
release queue item on exception (self._ready = True)
1.2.2
upd type hints
1.2.1
print -> log
1.2.0
_db_query_pretty_msg, msg 'DB query from queue...'
1.1.0
'Added' msg
1.0.0
init
"""

_global_queue = deque()  # type: deque # with q_ids
_global_queue_items = {}  # type: Dict[str, QueueItem]

_lock = threading.Lock()
# to stop from outer scope
_stop_thread = False

# Global flag to start from the code,
# used by _start_thread_once()
_is_started = False


def _start_thread_once():
    # If daemon=True, then this thread will be closed if MainThread falls
    # If daemon=False, then this thread will be running even if MainThread already exited
    # For reliability purposes, it is better to use daemon=False (always wait to be explicitly finished).
    # Meantime, if the code crashed out of try/except (i.e. import errs)
    # when QueueSimpleThread already started, then the
    # app will not finish (because the code won't `queue_simple.wait_finishing()`).
    # SOLUTION:
    # start the queue explicitly from the calling code (from `queue_simple.add()`),
    # it will be started once from the 1st call.
    # `queue_simple.wait_finishing()` must be in outer `finally` block of try/except
    # in the end of the app
    global _is_started
    with _lock:
        if not _is_started:
            log('Start queue thread')
            thread = threading.Thread(target=_loop_queue, name='QueueSimpleThread')
            thread.start()
            _is_started = True


class QueueItem:
    """QueueItem to call fn with fn_args"""

    def __init__(self, fn, fn_args, info=''):
        """
        :param fn: function to call
        :param fn_args: arguments for the fn
        :param info: optional text message describing the item
        """
        self.fn = fn
        self.fn_args = fn_args
        self.info = info

        self._ready = False
        self._result = None

    def ready(self) -> bool:
        return self._ready

    def get(self):
        return self._result

    def execute(self):
        try:
            self._result = self.fn(*self.fn_args)
        finally:
            self._ready = True


def _db_query_pretty_msg(db_query: str) -> str:
    """
    Expects a query with leading comment like
    `-- useful comment
    SELECT....`

    This comment will be used as msg
    """
    rows = db_query.strip().split('\n')
    if rows:
        return rows[0][:120]
    return ''


def add(fn: Callable, db_query: str, return_fields: Sequence) -> str:
    _start_thread_once()  # first start
    q_id = str(uuid.uuid4())
    fn_args = (db_query, return_fields)
    info = _db_query_pretty_msg(db_query)

    q_item = QueueItem(fn, fn_args, info)
    # print('DB query to queue {}: "{}..."'.format(q_id, q_item.info))

    with _lock:
        _global_queue_items[q_id] = q_item

    with _lock:
        _global_queue.append(q_id)

    return q_id


def get(q_id: str):
    item = _global_queue_items.get(q_id)  # type: Optional[QueueItem]
    if not item:
        return None

    result = item.get()
    # delete item to free memory
    try:
        with _lock:
            del _global_queue_items[q_id]
    except:
        # already deleted
        pass

    return result


def ready(q_id: str):
    item = _global_queue_items.get(q_id)  # type: Optional[QueueItem]
    if not item:
        return None

    return item.ready()


def _process_queue():
    with _lock:
        try:
            q_id = _global_queue.popleft()
        except IndexError:
            return

    q_item = _global_queue_items[q_id]
    log('DB query from queue {}: "{}..."'.format(q_id, q_item.info))
    # blocking command - this is that we need here
    q_item.execute()


def _loop_queue():
    while True:
        _process_queue()
        if _stop_thread:
            # stop on empty queue if flag set to True
            if not _global_queue_items:
                break
        time.sleep(0.05)


def wait_finishing():
    """Stop thread from outer scope in the end of the app.
    The thread will stop on empty queue and release the app"""
    global _stop_thread
    _stop_thread = True

