"""Functions for working with colors.
"""
import random


def blend_colors(base_color, added_color, blend):
    return tuple(
        int(base + (added - base) * blend)
        for (base, added) in zip(base_color, added_color)
    )


def get_color_vary_ns(variation_amount, min_n=None, max_n=None):
    rand_floats = [random.random() for _ in range(3)]
    rand_sum = sum(rand_floats)
    half_amount = variation_amount // 2
    rand_ns = [
        int(rand / rand_sum * variation_amount) - half_amount
        for rand in rand_floats
    ]
    increase_by = min_n - min(rand_ns)
    if increase_by > 0:
        rand_ns = [n + increase_by for n in rand_ns]
    decrease_by = max_n - max(rand_ns)
    if decrease_by < 0:
        rand_ns = [n + decrease_by for n in rand_ns]
    return rand_ns + [0]
