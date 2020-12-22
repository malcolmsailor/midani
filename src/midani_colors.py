"""Functions for working with colors.
"""


def blend_colors(base_color, added_color, blend):
    return tuple(
        int(base + (added - base) * blend)
        for (base, added) in zip(base_color, added_color)
    )
