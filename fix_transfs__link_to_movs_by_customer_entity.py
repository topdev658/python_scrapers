import datetime
import sys

from custom_libs.transfers_linker import TransfersLinker
from custom_libs.db import queue_simple

__version__ = '1.1.0'
__changelog__ = """
1.1.0
call TransfersLinker with upd args
1.0.0
init
"""

if __name__ == '__main__':
    print('***** START *****')
    start = datetime.datetime.now()
    customer_id = int(sys.argv[1])
    fin_entity_name = sys.argv[2]
    transfers_linker = TransfersLinker(
        db_customer_id=customer_id,
        fin_entity_name=fin_entity_name
    )
    transfers_linker.link_transfers_to_movements()
    finish = datetime.datetime.now()
    print('**** DONE in {} *****'.format(finish - start))
    queue_simple.wait_finishing()
