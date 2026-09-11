"""Signature 06: mutable default argument bug.

add_item's default cart list is created once at function definition time
and shared across every call that does not pass its own cart.
"""


def add_item(item, cart=[]):  # BUG: mutable default shared across calls
    cart.append(item)
    return cart
