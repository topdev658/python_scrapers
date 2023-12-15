"""
The script is supposed to be running each minute by cron.
If the current time (HH:MM) is exact as read_start_time returns, then
save_next_start_time is executed and the scraper starts
"""

import random
import sys
from datetime import datetime, time

import main_launcher

# Local time
ALLOWED_HOURS = {'from': 8, 'to': 21}
ALLOWED_MINUTES = {'from': 15, 'to': 45}


def filename(customer_id: int) -> str:
    return 'next_random_start_u{}'.format(customer_id)


def save_next_start_time(customer_id: int, at: time):
    with open(filename(customer_id), 'w') as f:
        f.write(at.strftime('%H:%M'))


def read_start_time(customer_id: int) -> time:
    try:
        with open(filename(customer_id)) as f:
            val = f.read().strip()
            return datetime.strptime(val, '%H:%M').time()
    except FileNotFoundError:
        return datetime.now().time()  # 1st time


def gen_next_start_time() -> time:
    now = datetime.now()  # local
    hour = now.hour
    next_hour = hour + 1
    if next_hour > ALLOWED_HOURS['to']:
        next_hour = ALLOWED_HOURS['from']
    next_minute = random.randint(ALLOWED_MINUTES['from'], ALLOWED_MINUTES['to'])
    return time(hour=next_hour, minute=next_minute)


def cmp_hm(t1: time, t2: time) -> bool:
    return (t1.hour == t2.hour) and (t1.minute == t2.minute)


if __name__ == '__main__':
    parser, args = main_launcher.parse_cmdline_args()
    user_id = args.user_id
    if not user_id:
        print('-u must be specified! ABORT')
        parser.print_help()
        sys.exit(1)
    if not cmp_hm(datetime.now().time(), read_start_time(user_id)):
        print("It's not a start time. Abort")
    else:
        print('Start time detected. Starting')
        save_next_start_time(user_id, gen_next_start_time())
        main_launcher.main('main_launcher')  # default start
