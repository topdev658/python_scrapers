from typing import Iterable

__version__ = '1.3.1'
__changelog__ = """
1.3.1
more doctests
1.3.0
any_el_endswith
1.2.0
new uniq_tail w/o uniq_seq_len param
1.1.0
uniq_tail: short path for empty base
"""


def is_sublist(basic: list, sub: list) -> bool:
    """Checks for containing list elements with exact the same ordering

    >>> is_sublist([], [])
    True

    >>> is_sublist([1, 2, 3], [1, 2, 3])
    True

    >>> is_sublist([9, 8, 7, 1, 2, 4, 5], [])
    True

    >>> is_sublist([9, 8, 7, 1, 2, 3, 4, 5], [1, 2, 3])
    True

    # tricky case - similar beginning in several places
    # but only one part is exactly the same
    >>> is_sublist([1, 2, 4, 1, 2, 3], [1, 2, 3])
    True

    >>> is_sublist([1, 2], [1, 2, 3])
    False

    >>> is_sublist([1, 2, 4, 1, 2, 4], [1, 2, 3])
    False

    >>> is_sublist([9, 8, 7, 1], [1, 2, 3])
    False

    >>> is_sublist([], [1, 2, 3])
    False
    """

    if not sub:
        return True

    if basic == sub:
        return True

    basic_len = len(basic)
    for ix in [ix for ix, basic_val in enumerate(basic) if basic_val == sub[0]]:
        ix_to = ix + len(sub)
        if ix_to <= basic_len:
            if basic[ix:ix_to] == sub:
                return True

    return False


def uniq_tail(base: list, tail: list) -> list:
    """Finds the unique rest of the tail.
    It doesn't depend on uniq_seq_len (as the previous implementation)

    :param base: existing list
    :param tail: the list where we should get only unique rest (= tail of the tail)

    >>> base = [1, 2, 3, 4, 6, 7, 8]
    >>> uniq_tail(base, [7, 8, 9])
    [9]

    >>> base = [1, 2, 3, 4, 6, 7, 8]
    >>> uniq_tail(base, [7, 8, 9, 10])
    [9, 10]

    >>> base = [1, 2, 3, 4, 6, 7, 8]
    >>> uniq_tail(base, [])
    []

    >>> base = [1, 2, 3, 4, 6, 7, 8, 9]
    >>> uniq_tail(base, [7, 8, 9])
    []

    >>> base = [1, 2, 3, 4, 6, 7, 8, 9]
    >>> uniq_tail(base, [7, 8, 9, 10, 11])
    [10, 11]

    >>> base = [1, 2, 3, 4, 6, 7, 8, 7, 8]
    >>> uniq_tail(base, [7, 8, 9, 10])
    [9, 10]

    >>> base = [1, 2, 3, 4, 6, 7, 8, 9, 7, 8]
    >>> uniq_tail(base, [7, 8, 9, 10])
    [9, 10]

    >>> base = [1, 2, 3, 4, 6, 7, 8, 7]
    >>> uniq_tail(base, [7, 8, 9, 10])
    [8, 9, 10]

    >>> base = [1, 2, 3]
    >>> uniq_tail(base, [4, 5, 6])
    [4, 5, 6]

    >>> base = [1, 2, 3]
    >>> uniq_tail(base, [])
    []
    """

    if not base:
        return tail

    if not tail:
        return []

    # Check directly 'tail' == tail of the 'base'
    if len(tail) <= len(base):
        if tail == base[-len(tail):]:
            return []

    uniq_ix = 0
    for i, _ in enumerate(tail):
        # Look for non-uniq part
        if not is_sublist(base, tail[:i + 1]):
            uniq_ix = i
            if i == 0:
                break
            # Check previous: uniq part should be in the end of the base.
            for j in range(uniq_ix - 1, -1, -1):  # [uniq_ix, ..., 0]
                # Compare corresponding elements,
                # for example, if uniq_ix == 2
                # => should compare indexes:
                # tail[1] == base[-1], tail[0] == base[-2]
                if tail[j] != base[j - uniq_ix]:
                    uniq_ix = j
    return tail[uniq_ix:]


def join_uniq_tail(base: list, tail: list) -> list:
    """
    >>> join_uniq_tail([1,2,3], [3,4,5])
    [1, 2, 3, 4, 5]

    >>> join_uniq_tail([1,2,3], [4,5])
    [1, 2, 3, 4, 5]
    """
    tail_uniq = uniq_tail(base, tail)
    joined = base + tail_uniq
    return joined


def any_el_endswith(els: Iterable[str], suffix: str) -> bool:
    """:return True if any of els ends with suffix

    >>> els = ["test1", "test2", "test3"]
    >>> any_el_endswith(els, "test")
    False
    >>> any_el_endswith(els, "test1")
    True
    >>> any_el_endswith(els, "st1")
    True
    """
    return any(el.endswith(suffix) for el in els)
