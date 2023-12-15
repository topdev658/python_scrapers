"""Global queue manager.
Results can be logged with output like
2017-11-20 11:38:46:INFO:Queue: DB customer None: fin_entity_access None: <function test_fn at 0x7f96173501e0>: True
Use wait_finishing() in the end of global process (main_launcher)
"""

import random
import threading
import time
import traceback
from collections import deque
from concurrent import futures

from custom_libs import scrape_logger
from project import settings as project_settings

__version__ = '2.0.0'

__changelog__ = """
2.0.0
renamed to fix python's queue import in debugger
1.4.0
new wait_finishing to handle possible rare 'hanged' cases 
1.3.0
add delay before return from wait_finishing
1.2.0
logger.info if result
1.1.1
DB_QUEUE_CONCURRENT_WORKERS const renamed
1.1.0
logging
project settings integration
"""

IS_LOG_QUEUE_RESULTS = False
IS_DEBUG_QUEUE = False

global_queue = deque()
lock = threading.Lock()
is_processing = False


def add(*args):
    with lock:
        global_queue.append(args)
    process()


def process_serial():
    global is_processing
    # Check if already processing from another call, just return
    if is_processing:
        return

    with lock:
        is_processing = True

    while True:
        with lock:
            try:
                first = global_queue.popleft()
            except IndexError:
                is_processing = False
                return

        fn = first[0]
        args = first[1:]
        time.sleep(random.random())  # delay for tests
        fn(*args)

        with lock:
            is_processing = False


def process():
    logger = scrape_logger.ScrapeLogger('Queue', None, None)

    global is_processing
    # Check if already processing from another call, just return
    if is_processing:
        return

    with lock:
        is_processing = True

    # read the queue to list
    l = []
    while True:
        with lock:
            try:
                l.append(global_queue.popleft())
            except IndexError:
                break

    with futures.ThreadPoolExecutor(max_workers=project_settings.DB_QUEUE_CONCURRENT_WORKERS) as executor:
        futures_dict = {
            executor.submit(fn_w_args[0], *fn_w_args[1:]): fn_w_args[0]
            for fn_w_args in l
        }

        for future in futures.as_completed(futures_dict):
            future_id = futures_dict[future]
            try:
                if IS_LOG_QUEUE_RESULTS or IS_DEBUG_QUEUE:
                    result = future.result()
                    if result:
                        logger.info('{}: {}'.format(future_id, result))
                else:
                    future.result()
            except Exception as exc:
                # Cannot raise exception upper, need to process it here
                logger.error('Queue: process: EXCEPTION:\n{}'.format(traceback.format_exc()))

    with lock:
        is_processing = False


def wait_finishing():
    """need to call process() to finish queue
    launch this function in the end of main caller (main_laucher)
    """
    while global_queue != deque([]) or is_processing:
        if IS_DEBUG_QUEUE:
            print('call "process()"')
        process()
        time.sleep(0.1)


# ##############  testing  ##############


def test_fn(*args):
    time.sleep(random.random() * 2)  # delay for tests
    print(args)
    return True


def test_serial():
    add(test_fn, 1, 2)
    add(test_fn, 3, 4)
    add(test_fn, 5, 6)
    add(test_fn, 7, 8)


def test_parallel():
    def some_useful_func(*args):
        add(test_fn, *args)

    args1 = [
        (1, 2),
        (3, 4),
        (5, 6),
        (7, 8),
        (9, 10),
        (11, 12),
        (13, 14),
        (15, 16),
        (17, 18),
    ]

    print('*** START STEP 1 ***')

    with futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.map(some_useful_func, args1)

    print('*** START STEP 2 ***')

    args2 = [
        ('a', 'b'),
        ('c', 'd'),
        ('e', 'f'),
        ('g', 'h'),
        ('i', 'j'),
    ]

    with futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.map(some_useful_func, args2)


if __name__ == '__main__':
    print('=== Start testing ===')
    # print('Test serial')
    # test_serial()
    print('Test parallel')
    test_parallel()
    print('Wait finishing')
    wait_finishing()
    print('=== DONE ===')
