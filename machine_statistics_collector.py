"""
OUTPUT: date time cpu_usage% total_memory_usage%
"""

import psutil
import time
import datetime
import os

DELAY_MILLISECONDS = 250  # ms
LOG_FOLDER_PATH = 'logs/machine_stat'
LOG_FILE_PREFIX = 'machine_stat'  # will be saved as LOG_FILE_PREFIX__2017_01_01


__version__ = '1.2.1'

__changelog__ = """
1.2.1
upd log folder path
1.2.0
now -> utcnow. to use utc always
1.1.0
utcnow -> now to be the same as in the logs
"""


def curr_time():
    now = datetime.datetime.utcnow()
    return now.strftime('%H:%M:%S')    # Y-%m-%d\t


def log_fname_date():
    now = datetime.datetime.utcnow()
    return now.strftime('%Y_%m_%d')


def cpu_percent():
    return psutil.cpu_percent()


def swap_memory():
    sm = psutil.swap_memory()
    sm_total = sm.total
    sm_used = sm.used
    return sm_total, sm_used


def virtual_memory():
    vm = psutil.virtual_memory()
    vm_total = vm.total
    vm_used = vm.used
    return vm_total, vm_used


def memory_percent():
    st, su = swap_memory()
    vt, vu = virtual_memory()

    memory_used_percent = round(((su + vu) / (st + vt) * 100), 1)
    return memory_used_percent


def log(text):
    """
    starts new file each day
    """
    # print(text)
    fname = '{}__{}'.format(LOG_FILE_PREFIX, log_fname_date())
    fpath = os.path.join(LOG_FOLDER_PATH, fname)
    with open(fpath, 'a') as f:
        f.write(text + '\n')


def main():
    while True:
        log('{:8}\t{:5}\t{:5}'.format(curr_time(), cpu_percent(), memory_percent()))
        time.sleep(DELAY_MILLISECONDS/1000)


if __name__ == '__main__':
    main()
