"""Signature 06: mutable default argument bug, fixed.

add_item defaults cart to None and allocates a fresh list per call.
"""


def add_item(item, cart=None):
    if cart is None:
        cart = []
    cart.append(item)
    return cart


REPRO_CASES = [
    (("apple",), ["apple"]),
    (("banana",), ["banana"]),
]

MUTANTS = [
    ("reintroduce the shared mutable default",
     "def add_item(item, cart=None):\n    if cart is None:\n        cart = []\n",
     "def add_item(item, cart=[]):\n"),
    ("swap append for a no-op assignment",
     "cart.append(item)", "cart = cart + []"),
]
