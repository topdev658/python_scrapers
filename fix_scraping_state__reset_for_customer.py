"""
This module accepts user ID as a positional arg and resets scraping state for
the customer and his/her accesses
"""

import sys
import time

from custom_libs import state_reset
from custom_libs.db import queue_simple


def main():
    args = sys.argv
    try:
        if len(args) < 2:
            print('Specify user ID to reset state: python fix_scraping_state__reset_for_customer.py 12345')
            sys.exit(1)
        uid = int(sys.argv[1])
        print('State reset: START: {}'.format(uid))
        state_reset.reset_forced(uid)
        print('State reset: DONE')
    finally:
        queue_simple.wait_finishing()
        time.sleep(3)


if __name__ == '__main__':
    main()
