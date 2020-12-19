"""Provides tuning and spelling functions for efficient_rhythms2.py."""

import math
import numbers

# import numpy as np

# import music_checks
# import mal_iter
# import mal_misc

# ALPHABET = "fcgdaeb"

# for EastWest, SIZE_OF_SEMITONE should be 4096
# for Vienna, SIZE_OF_SEMITONE should be 8192

SIZE_OF_SEMITONE = 4096
#
#
# def pitch_to_hertz(
#     pitch, tet=12, reference_hz=261.625565, reference_pitch=None
# ):
#     """Converts midi number(s) to a frequency.
#
#     Args:
#         pitch: midi number. Doesn't have to be a whole number. Can also be
#             a numpy array, in which case a numpy array will be returned.
#
#     Keyword args:
#         reference_hz: optional reference frequency.
#             Default: 261.625565 ("Middle C")
#         reference_pitch: optional reference pitch. Default: 5 * tet
#
#     Returns:
#         number or numpy array
#     """
#     music_checks.tet(tet)
#     if reference_pitch is None:
#         reference_pitch = 5 * tet
#
#     out = reference_hz * (2 ** (1 / tet)) ** (pitch - reference_pitch)
#
#     if np.equal(out, float("inf")).any():
#         raise OverflowError("Pitch is too large relative to temperament")
#
#     return out
#
#     # return round((reference_hz*(2**(1/tet))**(pitch-reference_pitch)),precision)
#
#
# def hertz_to_pitch(
#     hertz, tet=12, reference_hz=261.625565, reference_pitch=None, rounded=True
# ):
#     music_checks.hertz(hertz)
#     music_checks.tet(tet)
#     if reference_pitch is None:
#         reference_pitch = 5 * tet
#
#     out = (
#         np.log(hertz / reference_hz) / np.log(2 ** (1 / tet)) + reference_pitch
#     )
#     if rounded:
#         return np.floor(out + 0.5).astype(int)
#     else:
#         return out
#
#
# def finetune_pitch_bend_tuple(
#     pitch_bend_tuple, fine_tune, size_of_semitone=SIZE_OF_SEMITONE
# ):
#     new_midi_num = pitch_bend_tuple[0]
#     new_pitch_bend = round(
#         pitch_bend_tuple[1] + fine_tune / 100 * size_of_semitone
#     )
#     while abs(new_pitch_bend) > size_of_semitone / 2:
#         if new_pitch_bend > 0:
#             new_midi_num += 1
#             new_pitch_bend = new_pitch_bend - size_of_semitone
#         else:
#             new_midi_num -= 1
#             new_pitch_bend = new_pitch_bend + size_of_semitone
#
#     return new_midi_num, new_pitch_bend
#
#
def twelve_tet_midi_num_to_pitch_bend_tuple(
    midi_num, size_of_semitone=SIZE_OF_SEMITONE
):

    closest_whole_number = round(midi_num)
    pitch_bend = int((midi_num - closest_whole_number) * size_of_semitone)

    # I don't know if the next lines are really necessary
    while abs(
        midi_num - closest_whole_number - (pitch_bend + 1) / size_of_semitone
    ) < abs(midi_num - closest_whole_number - (pitch_bend) / size_of_semitone):
        pitch_bend += 1
    while abs(
        midi_num - closest_whole_number - (pitch_bend - 1) / size_of_semitone
    ) < abs(midi_num - closest_whole_number - (pitch_bend) / size_of_semitone):
        pitch_bend -= 1

    return (closest_whole_number, pitch_bend)


def return_pitch_bend_tuple_dict(
    tet, origin=0, size_of_semitone=SIZE_OF_SEMITONE
):
    """Returns a dictionary of form
            (pitch_number: (12-tet midinum, pitch_bend))

    Keyword args:
        - origin: the 12 - tet pitch class from which the relevant pitches
            will be calculated. (Should probably always be 0 (C).)
    """

    def _12_tet_pitch_classes(tet, origin=0):
        # origin = 0 builds scale from C as starting PC.
        step_size = 12 / tet
        pitch_classes = [(i * step_size) + origin for i in range(tet)]
        return pitch_classes

    def _12_tet_midi_nums(tet, origin=0):
        pitch_classes = _12_tet_pitch_classes(tet, origin % 12)
        pitches = []
        for octave in range(11):
            pitches += [
                pitch_class + (octave * 12) for pitch_class in pitch_classes
            ]
        return pitches

    twelve_tet_midi_nums = _12_tet_midi_nums(tet, origin)

    pitch_bend_tuple_dict = {}
    for pitch in range(tet * 11):
        pitch_bend_tuple_dict[pitch] = twelve_tet_midi_num_to_pitch_bend_tuple(
            twelve_tet_midi_nums[pitch]
        )

    return pitch_bend_tuple_dict


# @mal_iter.nested
# def get_just_pc(rational):
#     """Converts "just pitch(es)" to a "just pc(s)".
#
#     "Just pc's" are in the interval [1, 2). C = 1.0.
#
#     Args:
#         rational: float, Fraction, or arbitrarily deep/nested list-like.
#
#     Returns:
#         rational or list-like of rationals.
#     """
#     if rational <= 0:
#         raise ValueError("Just pitch must be greater than 0")
#     while rational < 1:
#         rational *= 2
#     while rational >= 2:
#         rational /= 2
#     return rational
#
#
# @mal_iter.nested
# def approximate_just_interval(rational, tet):
#     """Approximates given rational(s) in given equal temperament.
#
#     Can approximate intervals, pitches, or pitch-classes.
#         - Ascending intervals are > 1; descending intervals in (0, 1).
#         - When approximating pitches, C4 is 2**5. (Mnemonic: C4 is also
#             12 * 5 = 60.)
#         - When approximating pitch-classes, rational should be in [1, 2).
#
#     Args:
#         rational: float, Fraction, or arbitrarily deep/nested list-like.
#         tet: integer.
#
#     Returns:
#         integer or list-like of integers.
#     """
#
#     if rational < 1:
#         lower_power_of_two = 0
#         while 2 ** lower_power_of_two > rational:
#             lower_power_of_two -= 1
#         upper_power_of_two = lower_power_of_two + 1
#
#     else:
#         upper_power_of_two = 0
#         while 2 ** upper_power_of_two < rational:
#             upper_power_of_two += 1
#         lower_power_of_two = upper_power_of_two - 1
#
#     lower_power = lower_power_of_two * tet
#     upper_power = upper_power_of_two * tet
#
#     comma = 2 ** (1 / (tet * 2))
#
#     while True:
#
#         if upper_power - lower_power == 1:
#             upper_interval = 2 ** (upper_power / tet)
#             if (
#                 max(rational, upper_interval) / min(rational, upper_interval)
#             ) < comma:
#                 return upper_power
#             return lower_power
#
#         middle = (upper_power + lower_power) // 2
#         middle_interval = 2 ** (middle / tet)
#         if (
#             max(rational, middle_interval) / min(rational, middle_interval)
#         ) < comma:
#             return middle
#
#         if rational > middle_interval:
#             lower_power = middle
#         else:
#             upper_power = middle
#
#
# # def approximate_12_tet_pitch(pitch, tet):
# # Deprecated in favor of change_temperament
# #     """Approximates a 12-tet pitch in the specified temperament.
# #     """
# #     octave = pitch // 12
# #     pc = pitch % 12
# #     new_p = octave * tet + round((pc / 12) * tet)
# #     return new_p
#
#
# @mal_iter.nested
# def change_temperament(pitch, source_tet, dest_tet):
#     """Finds the closest pitch(es) in dest_tet to pitch(es) in source_tet.
#
#     Args:
#         pitch: integer, or arbitrarily deep/nested list-like. Can also be
#             a pitch-class.
#         source_tet: integer.
#         dest_tet: integer.
#
#     Returns:
#         integer or list-like of integers.
#     """
#     octave = pitch // source_tet
#     pc = pitch % source_tet
#     new_p = octave * dest_tet + round((pc / source_tet) * dest_tet)
#     return new_p
#
#
# # @mal_iter.nested
# # def temper_pitch_materials(item, tet, integers_in_12_tet=False):
# # Deprecated in favor of just using approximate_just_interval or
# # change_temperament directly.
# #     """Temper arbitrarily deep/nested list-like of pitches.
# #
# #     C4 is 2**5. (Mnemonic: C4 is also 12 * 5 = 60.)
# #
# #     Args:
# #         item: list-like of just pitches.
# #     """
# #     if isinstance(item, int):
# #         if integers_in_12_tet:
# #             pitch = approximate_12_tet_pitch(item, tet)
# #         else:
# #             pitch = item
# #         return pitch
# #
# #     new_pitch = approximate_just_interval(
# #         item, tet=tet)
# #     return new_pitch
#
#
# def temper_pitch_materials_in_place(item, tet, integers_in_12_tet=False):
#     try:
#         iter(item)
#         iterable = True
#     except TypeError:
#         iterable = False
#     if iterable:
#         if not isinstance(item, list):
#             raise TypeError(
#                 "All iterables passed to "
#                 "temper_pitch_materials_in_place must be lists."
#             )
#         copy_of_item = item.copy()
#         item.clear()
#         for sub_item in copy_of_item:
#             sub_item = temper_pitch_materials(
#                 sub_item, tet, integers_in_12_tet=integers_in_12_tet
#             )
#             item.append(sub_item)
#         return  # pylint: disable=inconsistent-return-statements
#
#     if isinstance(item, int):
#         if integers_in_12_tet:
#             pitch = approximate_12_tet_pitch(item, tet)
#         else:
#             pitch = item
#         return pitch
#
#     new_pitch = approximate_just_interval(item, tet=tet)
#     return new_pitch
#
#
# if __name__ == "__main__":
#     print(temper_pitch_materials([1.0, 2.0, 4.0, 8.0, 16.0, 32.0], 12))
#
#     breakpoint()
