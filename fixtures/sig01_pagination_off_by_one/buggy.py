"""Signature 01: pagination fencepost error.

page_slice drops the last item of every page because the upper bound of
the slice is computed one short.
"""


def page_slice(items, page, page_size):
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be >= 1")
    start = (page - 1) * page_size
    end = page * page_size - 1  # BUG: off by one, drops the last element
    return items[start:end]
