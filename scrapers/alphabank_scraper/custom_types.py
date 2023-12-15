from collections import namedtuple

AccProduct = namedtuple('AccProduct', [
   'account_no',
   'product_id',
   'type'
])


MovsPaginationParams = namedtuple('MovsPaginationParams', [
   'has_more_pages',
   'LastPageIndex_param',
   'LastExtraitKey_param'
])
