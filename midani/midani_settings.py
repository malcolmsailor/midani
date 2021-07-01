"""Provides Settings object for controlling animation parameters.
"""

import ast
import collections
import dataclasses
import itertools
import math
import numbers
import os
import random
import typing

from . import midani_colors

# TODO document scaled pixels
# TODO delete now_line
# TODO make folders if they don't exist
# TODO setting to specify path for temporary R files?
# TODO why do pngs (like those for the efficient_rhythms docs) have "outlines"
#   visible?

DEFAULT_CHANNEL_SETTINGS = {
    "l_padding": 0.1,
    "h_padding": 0.1,
}

TEMP_R_SCRIPT = "midani{:06d}.R"

DEFAULT_SHADOW_POSITIONS = lambda: []

DEFAULT_PIXEL_WIDTH = 1280


class ShadowPositions:
    def __init__(
        self,
        pixel_width,
        frame_len,
        shadow_x,
        shadow_y,
        cline_shadow_x=None,
        cline_shadow_y=None,
    ):
        self.shadow_x = shadow_x * frame_len / DEFAULT_PIXEL_WIDTH
        self.shadow_y = shadow_y * pixel_width / DEFAULT_PIXEL_WIDTH
        if cline_shadow_x is None:
            self.cline_shadow_x = self.shadow_x
        else:
            self.cline_shadow_x = (
                cline_shadow_x * frame_len / DEFAULT_PIXEL_WIDTH
            )
        if cline_shadow_y is None:
            self.cline_shadow_y = self.shadow_y
        else:
            self.cline_shadow_y = (
                cline_shadow_y * pixel_width / DEFAULT_PIXEL_WIDTH
            )


PER_VOICE_COLORS = (
    "shadow_color",
    "highlight_color",
    "con_line_offset_color",
    # "bracket_color",
)

GLOBAL_COLORS = (
    "intro_bg_color",
    "outro_bg_color",
    "annot_color",
    "lyrics_color",
)

PER_VOICE_COLOR_LISTS = ("color_loop",)
GLOBAL_COLOR_LISTS = ("color_palette", "bg_colors")

DEFAULT_OUTPUT_PATH = "midani_output"
DEFAULT_TEMP_R_PATH = ".temp_r_files"


def read_settings_files_into_dict(settings_paths, use_eval):
    def _merge(dict1, dict2):
        for key, val in dict2.items():
            if (
                isinstance(val, dict)
                and key in dict1
                and isinstance(dict1[key], dict)
            ):
                dict2[key] = _merge(dict1[key], val)
        return dict1 | dict2

    out = {}
    for user_settings_path in settings_paths:
        print(f"Reading settings from {user_settings_path}")
        with open(user_settings_path, "r", encoding="utf-8") as inf:
            if use_eval:
                user_settings = eval(inf.read())
            else:
                user_settings = ast.literal_eval(inf.read())
        out = _merge(out, user_settings)
    return out


Bracket = collections.namedtuple(
    "Bracket",
    ("start", "end", "type", "text", "loop", "loop_end"),
    defaults=("", None, None),
)


@dataclasses.dataclass
class BracketSettings:
    """Stores settings for brackets."""

    # LONGTERM should there be a way of specifying global defaults for the
    # brackets? (So if we want all brackets to be the same height, we
    # don't have to specify individually for each one?)

    # pixel_width is used to normalize line_width and text_size
    # it shouldn't be provided separately by the user, but should be
    # taken from the frame resolution setting
    pixel_width: int
    above: bool = False
    color: typing.Union[  # pylint: disable=unsubscriptable-object
        typing.Tuple[int, int, int], typing.Tuple[int, int, int, int]
    ] = (
        255,
        255,
        255,
    )
    line_width: float = 5.0
    height: float = 1.0
    y_offset: float = 1.0
    x_offset: float = 0.0
    text_size: float = 3.0
    text_y_offset: float = 0.2
    tight: bool = False

    _colors = ("color",)

    def __post_init__(self):
        # LONGTERM replace this with calls to pixel_normalize inside
        # VoiceSettings or Settings?
        self.line_width *= self.pixel_width / DEFAULT_PIXEL_WIDTH
        self.text_size *= self.pixel_width / DEFAULT_PIXEL_WIDTH
        add_transparencies(self)


def post_init_helper(obj):
    """Called by both VoiceSettings and Settings"""
    obj.frame_note_start = (
        obj.note_start
        * obj.global_parent.frame_len
        * obj.global_parent.frame_position
    )
    obj.frame_note_end = (
        obj.note_end
        * obj.global_parent.frame_len
        * (1 - obj.global_parent.frame_position)
    )

    obj.frame_line_start = (
        obj.line_start
        * obj.global_parent.frame_len
        * obj.global_parent.frame_position
    )
    obj.frame_line_end = (
        obj.line_end
        * obj.global_parent.frame_len
        * (1 - obj.global_parent.frame_position)
    )

    if obj.max_connection_line_interval is None:
        obj.max_connection_line_interval = obj.tet

    obj.shadow_hl_strength = obj.highlight_strength * obj.highlight_shadows
    obj.bounce_radius = obj.bounce_size / 2
    obj.bounce_sin_factor = 2 * math.pi / obj.bounce_period
    for bracket_i, bracket in enumerate(obj.brackets):
        if not isinstance(bracket, Bracket):
            obj.brackets[bracket_i] = Bracket(*bracket)

    add_transparencies(obj)

    # LONGTERM allow different shadow positions on a per-voice basis?
    # self.num_shadows = len(self.shadow_positions)
    #
    # # The next line tells us whether we need to update shadow positions
    # if not all(
    #     [isinstance(item, ShadowPositions) for item in self.shadow_positions]
    # ):
    #     self.shadow_positions = [
    #         ShadowPositions(
    #             shadow_x=s[0] / self.w_factor,
    #             shadow_y=s[1] / self.out_height,
    #             cline_shadow_x=(s[2] if len(s) > 2 else s[0]) / self.w_factor,
    #             cline_shadow_y=(s[3] if len(s) > 3 else s[1]) / self.out_height,
    #         )
    #         for s in self.shadow_positions
    #     ]
    # self.max_shadow_x_time = max(
    #     [s.shadow_x for s in self.shadow_positions]
    #     + [s.cline_shadow_x for s in self.shadow_positions]
    #     + [0,]
    # )
    # self.min_shadow_x_time = min(
    #     [s.shadow_x for s in self.shadow_positions]
    #     + [s.cline_shadow_x for s in self.shadow_positions]
    #     + [0,]
    # )


def add_transparencies(obj):
    """Add transparency value to colors if absent."""
    try:
        obj._colors  # pylint: disable=protected-access
    except AttributeError:
        pass
    else:
        for color_name in obj._colors:  # pylint: disable=protected-access
            if len(getattr(obj, color_name)) < 4:
                setattr(
                    obj,
                    color_name,
                    tuple(
                        list(getattr(obj, color_name))
                        + [
                            255,
                        ]
                    ),
                )

    try:
        obj._color_lists  # pylint: disable=protected-access
    except AttributeError:
        pass
    else:
        for color_list in obj._color_lists:  # pylint: disable=protected-access
            if color_list == "bg_colors":
                opacity = 255
            else:
                try:
                    opacity = obj.default_note_opacity
                except AttributeError:
                    opacity = obj.global_parent.default_note_opacity
            val = getattr(obj, color_list)
            if val is None or isinstance(val, int):
                continue
            setattr(
                obj,
                color_list,
                tuple(
                    tuple(
                        list(tup)
                        + [
                            opacity,
                        ]
                    )
                    if len(tup) < 4
                    else tup
                    for tup in val
                ),
            )


class VoiceSettings:
    """Manages attribute access for voice settings.

    If an attribute is not found, looks in voice of which the voice is a
    duplicate, if any; otherwise, looks in global Settings object.
    """

    allowed_kwargs = (
        "color",
        "color_loop",
        "color_loop_var_amount",
        "connection_lines",
        "con_line_offset_color",
        "con_line_offset_prop",
        "max_connection_line_duration",
        "max_connection_line_interval",
        "no_connection_lines_between_simultaneous_notes",
        "connection_line_start_offset",
        "connection_line_end_offset",
        "line_start",
        "line_end",
        "con_line_width",
        "line_start_size",
        "line_end_size",
        "rectangles",
        "note_start",
        "note_end",
        "note_size",
        "note_width",
        "note_height",
        "note_start_width",
        "note_start_height",
        "note_end_width",
        "note_end_height",
        "start_scale_function",
        "end_scale_function",
        "highlight_strength",
        "highlight_start",
        "highlight_end",
        "highlight_color",
        "shadow_strength",
        "shadow_color",
        "shadow_scale",
        "shadow_scale_x",
        "shadow_scale_y",
        "highlight_shadows",
        "shadow_gradients",
        "shadow_gradient_offset",
        "max_flutter_size",
        "min_flutter_size",
        "max_flutter_period",
        "min_flutter_period",
        "bounce_type",
        "bounce_size",
        "bounce_period",
        "bounce_len",
        "brackets",
        "bracket_settings",
        "default_bracket_settings",
    )

    allowed_attributes = (
        "frame_note_start",
        "frame_note_end",
        "frame_line_start",
        "frame_line_end",
        "max_shadow_x_time",
        "min_shadow_x_time",
        "num_shadows",
        "shadow_hl_strength",
        "bounce_radius",
        "bounce_sin_factor",
    ) + allowed_kwargs

    _colors = PER_VOICE_COLORS
    _color_lists = PER_VOICE_COLOR_LISTS

    def __init__(self, voice_i, parent, **kwargs):
        self.parent = parent
        if isinstance(parent, Settings):
            self.global_parent = parent
        else:
            self.global_parent = parent.global_parent

        for arg, val in kwargs.items():
            if arg not in self.allowed_kwargs:
                raise ValueError(
                    f"'{arg}' is not a valid keyword-argument to VoiceSettings"
                )
            setattr(self, arg, val)
        self.getattr_func = self._getattr
        if "color" not in kwargs:
            self.color = self.global_parent.color_palette[
                voice_i % len(self.global_parent.color_palette)
            ]
        elif len(self.color) < 4:
            self.color = tuple(self.color) + (self.default_note_opacity)
        if isinstance(
            self.color_loop,  # pylint: disable=access-member-before-definition
            int,
        ):
            min_n = -min(self.color[:3])
            max_n = 255 - max(self.color[:3])
            out = []
            for _ in range(
                self.color_loop  # pylint: disable=access-member-before-definition
            ):
                out.append(
                    tuple(
                        [
                            min(255, max(c1 + c2, 0))
                            for c1, c2 in zip(
                                self.color,
                                midani_colors.get_color_vary_ns(
                                    self.color_loop_var_amount,
                                    min_n=min_n,
                                    max_n=max_n,
                                ),
                            )
                        ]
                    )
                )
            self.color_loop = out

        if "note_size" in dir(self):
            if (
                "note_width" not in dir(self)
                or self.note_width  # pylint: disable=access-member-before-definition
                is None
            ):
                self.note_width = self.note_size
            if (
                "note_height" not in dir(self)
                or self.note_height  # pylint: disable=access-member-before-definition
                is None
            ):
                self.note_height = self.note_size

        post_init_helper(self)
        if "bracket_settings" in dir(self):
            for name, kwargs in self.bracket_settings.items():
                self.bracket_settings[name] = BracketSettings(
                    self.out_width,
                    **(
                        self.parent.default_bracket_settings
                        | self.default_bracket_settings
                        | kwargs
                    ),
                )
            if self.parent.bracket_settings is not None:
                for name, br_setting in self.parent.bracket_settings.items():
                    if name in self.bracket_settings:
                        continue
                    self.bracket_settings[name] = br_setting

        self.getattr_func = self._getattr2

    def _getattr(self, name):
        return getattr(self.parent, name)

    def __getattr__(self, name):
        return self.getattr_func(name)

    def _getattr2(self, name):
        """After post_init runs, we overwrite __getattr__ with this function."""
        if name in self.allowed_attributes:
            return self._getattr(name)
        raise AttributeError(
            f"'{name}' is not a valid attribute for VoiceSettings"
        )


@dataclasses.dataclass
class Settings:
    """Settings for midi animation plotting.

    Can be indexed like a list or a tuple to get voice-specific settings. E.g.,
    settings[2] will get voice-specific settings for voice with index 2.

    Some settings are omitted from the description of keyword arguments below
    as they are unlikely to be of interest to the user (they are in a sense
    "private" to the script).

    There are two types of settings, "global" settings and "per-voice" settings:

    - Global settings always apply to the animation as a whole. An example is
    `intro`, which sets the length of time before the music begins.

    - Per-voice settings can be applied to individual "voices" (=tracks in the
    input midi file). They can also be provided as global defaults which apply
    whenever the setting is not explicitly set for an individual voice. An
    example is `connection_lines`, which controls whether lines are drawn
    connecting consecutive notes in a voice.

    An example of the usage of global and per-voice settings:

    ```
    {
        "intro": 5,  # Global setting
        "voice_settings": {  # dict of per-voice settings
            0: {
                "connection_lines": True,  # Sets "connection_lines" for voice 0
            }
        },
        "connection_lines": False,  # Sets global default for voices
                                    # This global default will not apply to
                                    # voice 0, which sets "connection_lines"
                                    # explicitly
    }
    ```

    For the most part, the settings below each heading below are either all
    global  or all per-voice. Which of these is the case is noted directly
    below each heading, as are several special cases.

    When these settings contain terms like "start" and "end", these refer to
    positions *on each frame*. E.g., `note_start` is how far from the left side
    of each frame notes should begin. But notes are moving to the left, so this
    is actually the last moment at which the note will occur---so from another
    perspective, it should be "note_end."

    Note on colors:
        In this script, colors are specified by 3- or 4-tuples of ints from
        0--255. The fourth, optional integer specifies the transparency. If it
        is omitted, then the color will be fully opaque.

    Keyword args:

        General
        =======

        All general settings are global.

        midi_fname: str. Path to input midi file to be animated. If a midi path
            is passed as a command-line argument to the script, this value will
            be ignored. If this value is not set, nor is a command-line path
            passed, the script will abort---it will have nothing to animate!

            It is also possible to pass a list of files. In that case, the
            tempos will be taken from the first file, but the notes will be
            taken from all files.
        midi_reset_start_to_0: bool. If True, then the first note in the input
            midi file will be adjusted to occur at time "0" (if it doesn't
            already).
            Default: False
        midi_tracks_to_voices: bool. If True, different tracks in the input
            midi will be mapped to different "voices" in the animation.
            Default: True
        midi_channels_to_voices: bool. If True, different channels in the input
            midi will be mapped to different "voices" in the animation.
            (It is possible for both `midi_tracks_to_voices` and
            `midi_channels_to_voices` to be True.)
            Default: False
        output_dirname: str. path to folder where output images will be created.
            If a relative path, will be created relative to the current
            directory. If the path does not exist, it will be
            created.
            Default: "midani_output"
        resolution: tuple of form (int, int). Resolution of output frames.
            Default (1280, 720)
        process_video: str. Possible values:
                "yes" : (Default) makes .mp4 video file using OpenCV
                "no" : doesn't make video file.
                "only" : makes .mp4 video file using OpenCV and skips the rest
                    of the script. (Note: in this case, the number of frames
                    will be inferred from the number of files that match the
                    png filename in `output_dirname`.)
        video_fname: str. Path to output video file. If a basename (i.e., with
            no directory component), will be written in directory
            `output_dirname`. If not passed, the video will be written in
            `output_dirname` with the same filename as `midi_fname`, except for
            the extension ".mp4". (If `midi_fname` is a list, then it will be
            named after the first item in the list.) Has no effect if
            `process_video` == "no".
        audio_fname: str. Path to input audio file. If passed, this audio file
            will be added to the output video file using ffmpeg. If ffmpeg is
            not found, a warning will be printed instead and no audio will be
            added. (If `process_video` == "no", this argument is
            ignored.) Note that if `midi_fname` is passed as a command-line
            argument, this keyword argument will be ignored; any audio file
            should then be passed as a command-line argument as well.
        clean_up_r_files: bool. If False, the R scripts output by this script
            will not be deleted (and so can be inspected).
            Default: True.
        clean_up_png_files: bool. If False, the png files output by this script
            will not be deleted (and so can be inspected). If `process_video`
            is "no", then this setting is ignored.
            Default: True.
        tet: int. Set temperament.
            Default: 12 (for 12-tone equal temperament.)
        seed: int. Seed for python's random module.
            Default: None.

        Frame
        ======

        All frame settings are global.

        frame_len: float. Length (in seconds) of each frame.
            (I.e., the time interval between the moment represented by the left
            side of the frame and the moment represented by the right side.)
            Default: 9.
        frame_increment: float. Time interval between frames. Reciprocal of
            frame rate per second.
            Default: 1/30.
        frame_position: float in the half-open interval [0, 1). Specifies the
            horizontal position of note attacks (i.e., "now") in the frame,
            where 0 is the left side of the frame and 1 the right. A value of 1
            will lead to division by zero errors (and would, in any case, cause
            notes to be invisible off the right side of the frame at the moment
            of their attack.)
            Default: 0.5

        Timing
        ======

        All timing settings are global.

        intro: float. Length of time in seconds that should precede `start_time`
            Default: 1.0
        outro: float. Length of time in seconds that should follow `end_time`
            Default: 1.0
        start_time: float. Notes before this time (in seconds) in the input
            midi file will be ignored (not drawn).
            NB start_time will be ignored if either of `start_bar` or
            `start_beat` is nonzero.
            Default: 0.0
        start_bar: int. Notes before this bar in the input midi file will be
            ignored (not drawn). If passed and nonzero, then `start_time` is
            ignored. Depends for its interpretation on `bar_length`, which must
            be passed a nonzero value as well, otherwise a ValueError will be
            raised.
            NB in accordance with usual musical practice, (and contrary to
            usual Python indexing), the first bar is bar "1".
            Default: 0
        start_beat: float. Notes before this beat in the input midi file will be
            ignored (not drawn). Can be used in combination with `start_bar`
            (e.g., to indicate "4th bar, 3rd beat") or on its own (which could
            be useful if the time signature changes frequently).
            NB in accordance with usual musical practice, (and contrary to
            usual Python indexing), the first beat is beat "1".
            Default: 0
        end_time: float. Notes after this time (in seconds) in the input
            midi file will be ignored (not drawn).
            NB end_time will be ignored if either of `end_bar` or
            `end_beat` is nonzero.
            Default: 0.0
        end_bar: int. Notes after this bar in the input midi file will be
            ignored (not drawn). If passed and nonzero, then `end_time` is
            ignored. Depends for its interpretation on `bar_length`, which must
            be passed a nonzero value as well, otherwise a ValueError will be
            raised.
            NB in accordance with usual musical practice, (and contrary to
            usual Python indexing), the first bar is bar "1".
            Default: 0
        end_beat: float. Notes after this beat in the input midi file will be
            ignored (not drawn). Can be used in combination with `end_bar`
            (e.g., to indicate "4th bar, 3rd beat") or on its own (which could
            be useful if the time signature changes frequently).
            NB in accordance with usual musical practice, (and contrary to
            usual Python indexing), the first beat is beat "1".
            Default: 0
        final_bar: int. `final_bar` and `final_time` are used to optionally set
            a beat/time after which the background should begin the transition
            to `end_bg_time` (e.g., to set this to the final note attack,
            rather than the final note release). If `final_bar` and `final_beat`
            are both 0, they are ignored.
            NB in accordance with usual musical practice, (and contrary to
            usual Python indexing), the first bar is bar "1".
            Default: 0
        final_beat: float. See `final_bar`.
            NB in accordance with usual musical practice, (and contrary to
            usual Python indexing), the first beat is beat "1".
            Default: 0
        bar_length: float. (Only) used to interpret `start_bar`, `end_bar`,
            and/or `final_bar`. If any of these latter are nonzero, it will
            raise a ValueError not to pass a nonzero value of this setting.
        scale_notes_from_attack: bool. If True, then notes and lines are scaled
            based on their attack time. Otherwise, they are scaled based on the
            midpoint between their attack and their release.
            Default: True

        Lyrics
        ======

        All lyrics settings are global.

        lyrics: dict of form float: str. The float keys are times in seconds;
            the string values is the lyric text that should occur at those times.
            Each lyric occurs until the time specified by the next lyric. To
            make a lyric go away, but not have another appear, use an empty
            string. The lyrics will be sorted by their associated times, so
            it is not necessary for this dictionary to be in order.
            Default: None
        lyrics_x: float between 0 and 1. Specifies horizontal frame position on
            which lyrics are centered. The far left is 0 and the far right is 1.
            Default: 0.5
        lyrics_y: float between 0 and 1. Specifies vertical frame position on
            which lyrics are centered. The bottom is 0 and the top is 1.
            Default: 0.1
        lyrics_color: tuple of form (int, int, int[, int]). Color for lyrics.
            Default: (255, 255, 255, 255).
        lyrics_size: float. Sets lyrics size by scaling the lyrics with the
            `cex` argument to the R `text` command.
            Default: 3.0

        Channels
        ========

        All channels settings are global.

        num_channels: int. Number of exclusive horizontal `channels` to place
            voices into. (For example, the winds and the strings could be placed
            into exclusive channels.)
            Default: 1
        channel_proportions: tuple of floats. Relative heights of channels.
            Channels are listed from top to bottom. Will be normalized, so
            heights don't have to sum to 1 or any other particular value. If
            this argument is omitted, then all channels will have the same
            height. If this argument is included, but its length does not equal
            `num_channels`, a ValueError will be raised.
        chan_assmts: dictionary of form {int: int}. Assigns voices (keys) to
            channels (values). Any missing voices will be assigned to channel 0.
            If omitted, all voices are assigned to channel 0. Channel 0 is the
            top channel.
        channel_settings: dictionary of form {int: dict}, where the int key is
            the index to a channel and the dictionary value provides per-channel
            settings as specified below. Any channels or settings omitted will
            be provided with the default settings.
                "l_padding" : float between 0 and 1. Indicates how much padding
                    should be provided below the lowest pitch of the channel
                    and the bottom of the channel, as a proportion of the
                    channel.
                    Default: 0.1
                "h_padding" : float between 0 and 1. Indicates how much padding
                    should be provided below the highest pitch of the channel
                    and the top of the channel, as a proportion of the
                    channel.
                    Default: 0.1

        Background
        ==========

        The background color can be either constant, or it can change at
        specified times. If it changes, it can either change suddenly or blend
        linearly from one color to the next.

        All background settings are global.

        If `bg_beat_times` is empty, or if `bg_beat_times_length` == 0, or if
        len(bg_colors) == 1, the background color will  be constant.

        bg_beat_times: list of numbers. Sets the times, in beats, between the
            arrival of each color in `bg_colors`. If 0 is not the first item
            in the list, the bg_color until the first time in the list will
            be the last color in `bg_colors`.
            Default: (0,)
        bg_beat_times_length: number. Sets the number of beats at which the list
            of times in `bg_beat_times` will repeat. E.g., if `bg_beat_times`
            is [0, 3] and `bg_beat_times_length` is 8, the effective background
            beat times inferred will be [0, 3, 8, 11, 16, 19, ...]. Essentially
            sets a "time signature" for `bg_beat_times`. If < than the largest
            number in `bg_beat_times`, strange things may happen.
            Default: 0
        bg_colors: a list of tuples of form (int, int, int, int), where each
            tuple is an RGB color.
            Default: [(32, 32, 32, 255), (192, 192, 192, 255)]
        bg_color_blend: boolean. If True, background colors scale linearly from
            one to the next. If False, background colors change suddenly.
            Default: True
        intro_bg_color: tuple of form (int, int, int). The RGB color at the
            start of the intro (if any), or during the complete intro, if
            `bg_color_blend` is False.
        outro_bg_color: tuple of form (int, int, int). The RGB color at the
            end of the outro (if any), or during the complete outro, if
            `bg_color_blend` is False.

        Global voice settings
        =====================

        These settings are all global; to set per-voice settings, use the
        "voice_settings" argument described below.

        voices_to_render: list-like of integer indices. Determines which
            "voices" (=tracks) in the input midi file to render. If empty, all
            voices are rendered.
            Default: empty.
        voice_order: list of integer indices. Specifies the order in which
            voices should be drawn. If empty, voices are written in the order
            in which they appear in the input midi file. If non-empty, any
            voices that are present (perhaps implicitly) in `voices_to_render`
            but are absent from this list will be appended to it in the order
            in which they appear in the input midi file.
            Default: empty.
        voice_order_reverse: boolean. If True, then `voice_order` will be
            reversed, *after* any missing values are added to it. This is mainly
            useful for drawing from lowest to highest midi files that are
            ordered from highest to lowest.
            Default: False
        voice_settings: dictionary. Keys are integer indices to voices (=tracks)
            in the input midi file. Values are themselves dictionaries of
            per-voice settings. See above for more on per-voice settings. See
            also `duplicate_voice_settings` below.
            Note that the per-voice setting `color` is a special case: if the
            `color` argument is not explicitly provided for a voice, the voice
            will be assigned the color from the global `color_palette` setting
            at the position specified by its integer index (modulo the length of
            the color palette), rather than any global value for `color`, which
            has never has any effect.
        duplicate_voice_settings: a dictionary of form {int, list of ints}. Keys
            are "parent" voices and settings are "child" voices. Any per-voice
            settings not explicitly set in the child voice will be taken from
            the parent voice. If they are not found in the parent voice, the
            search continues recursively until we reach the global settings. An
            exception is `color`, which must be specified explicitly for each
            voice, or it is taken from the global `color_palette`.
        p_displace: a dictionary of form {int, list of ints}. Keys are pitch
            intervals in semitones. Values are lists of indices to voices. The
            voices indicated will be displaced by the associated interval. This
            can be useful if, for example, the bass is widely separated from
            the other voices and it would be more visually appealing to bring
            it up an octave.
        color_palette: list of tuples of form (int, int, int, int) or
            (int, int, int). Ints are from 0 to 255 and the fourth optional
            integer species the transparency (if omitted, the opacity is
            specified by default_note_opacity).
            A palette of colors to which any voice not explicitly assigned a
            color will be assigned. Default is 16 colors drawn at random from
            matplotlib's `viridis` colorscheme.
        default_note_opacity: int from 0 to 255. Specifies the opacity of any
            note color that does not have an explicitly set opacity.
            (I.e., of any note color specified with a 3-tuple rather than a
            4-tuple.)



        Connection lines
        ================

        All connection line settings are per-voice or global.

        connection_lines: boolean. If True, "connection lines" are drawn
            between adjacent notes on the same track (subject to certain
            conditions, controlled by the subsequent keyword arguments).
            Default: True
        con_line_offset_color: tuple of form (int, int, int[, int]). An RGB
            color to blend with the color of the previous note, in order to
            define the color of the connection_lines.
            Default: (128, 128, 128, 255)
        con_line_offset_prop: float. Controls strength of blend of
            `con_line_offset_color`.
            Default: 0.0
        max_connection_line_duration: float. Maximum time interval in seconds
            over which connection lines will be drawn. (Where the start and
            end points of the lines are situated depends on
            connection_line_end_offset and connection_line_start_offset)
            NB that if a note that is long starts just before a note that is
            short, the line may appear to go "backwards" from the former to the
            latter.
            Default: 0.25
        max_connection_line_interval: float. Maximum pitch interval (in
            temperament as defined by `tet`) between notes for which a
            connection line will be drawn.
            By default, set to value of `tet` (i.e., one octave).
        no_connection_lines_between_simultaneous_notes: boolean. If True, then
            connection lines are not drawn between simultaneous notes in the
            same part.
            Default: True
        connection_line_start_offset: float. How far, in seconds, from the
            start of each note the x coordinate of the endpoint of the line
            joining it to the previous note should be. If, for a particular
            note, this value leads to an x coordinate that is greater than the
            midpoint of the note, it will be ignored in favor of the midpoint
            of the note. If not passed, then the start is always the midpoint
            of each note.
        connection_line_end_offset: float. How far, in seconds, from the
            end of each note the x coordinate of the endpoint of the line
            joining it to the next note should be. If, for a particular note,
            this value leads to an x coordinate that is smaller than the
            midpoint of the note, it will be ignored in favor of the midpoint
            of the note. If not passed, then the end is always the midpoint
            of each note.
        line_start: floats in closed interval [0, 1]. Determine where in the
            frame connection lines are first drawn, as a proportion of the
            distance between the start of the frame and "now" as indicated by
            `frame_position`.
            Default: 1.0
        line_end: floats in closed interval [0, 1]. Determine where in the
            frame connection lines are last drawn, as a proportion of the
            distance between the end of the frame and "now" as indicated by
            `frame_position`.
            Default: 1.0
        con_line_width: float. Width of connection lines at moment "now". If
            `line_start_size` or `line_end_size` != 1, then line width will be
            scaled linearly between `line_start` and "now", or between "now"
            and `line_end`.
            Default: 5.0
        line_start_size: float. Amount by which `con_line_width` should be
            scaled at `line_start`.
            Default: 1.0
        line_end_size: float. Amount by which `con_line_width` should be
            scaled at `line_end`.
            Default: 1.0


        Notes (or "rectangles")
        =======================

        All rectangle settings are per-voice or global.

        color: tuple of form (int, int, int, int) or (int, int, int). Only has
            an effect as a per-voice setting. If a voice does not have an
            explicit value for `color`, it will take its color from the
            global setting `color_palette` (see above). On the other hand,
            if a sequence of colors is passed to "color_loop", this argument
            is ignored.
        color_loop: an int, or a sequence of tuples of colors.
            If an int (the recommended usage for most use cases), a loop of that
            length will be created of variations on the color specified by
            `color` (or the relevant value in `color_palette`). The amount of
            variation is controlled by `color_loop_var_amount`.
            If a sequence, then explicitly sets a loop of colors.
        color_loop_var_amount: number. Controls how much variation to apply
            to create the colors in `color_loop`.
            Default: 128
        rectangles: boolean. If True, a "rectangle" (the usual piano-roll
            representation) is drawn for each note. Note that this sets
            a default that can be overridden on a per-voice basis.
            Default: True
        note_start: floats in closed interval [0, 1]. Determine where in the
            frame rectangles are first drawn, as a proportion of the
            distance between the start of the frame and "now" as indicated by
            `frame_position`.
            Default: 1.0
        note_end: floats in closed interval [0, 1]. Determine where in the
            frame rectangles are last drawn, as a proportion of the
            distance between the end of the frame and "now" as indicated by
            `frame_position`.
            Default: 1.0
        note_size: float. Factor by which notes should be scaled at
            moment "now". The base height of a note is 1 semitone, and the base
            width is its duration, so if > 1, rectangles will overlap each
            other, whereas if it is < 1, they will have extra spacing. If
            either `note_width` or `note_height` are nonzero,
            this argument is ignored in the width or height dimension,
            respectively (or both).
            Default: 1.
        note_width: float. Overrides `note_size` in x
            dimension.
        note_height: float. Overrides `note_size` in y
            dimension.
        note_start_width: float. Amount by which `note_size` should be
            scaled horizontally at `note_start`.
            Default: 1.0
        note_start_height: float. Amount by which `note_size` should be
            scaled vertically at `note_start`.
            Default: 1.0
        note_end_width: float. Amount by which `note_size` should be
            scaled horizontally at `note_end`.
            Default: 1.0
        note_end_height: float. Amount by which `note_size` should be
            scaled vertically at `note_end`.
            Default: 1.0
        start_scale_function, end_scale_function: callables. These functions
            will be called to determine how note and line size is scaled between
            their starts/ends respectively and "now". Default is linear. The
            callable needs to be able to handle zero values (e.g.,
            `lambda x: 1/x` will throw a ZeroDivisionError).
            Default: lambda x: x (i.e., linear)

        Highlight
        =========

        All highlight settings are per-voice or global.

        highlight_strength: float. Controls how strongly `highlight_color` is
            mixed with the current note color at moment "now".
            Default: 1.0
        highlight_start: float. Time in seconds when highlight should begin.
            The amount of `highlight_color` blended with the current note
            color will scale linearly from 0 beginning at this moment up to
            `highlight_strength` at "now".
            Default: 0.1
        highlight_end: float. Time in seconds when highlight should emd.
            The amount of `highlight_color` blended with the current note
            color will scale linearly from `highlight_strength` at "now" down
            to 0 at this moment.
            Default: 0.25
        highlight_color: tuple of form (int, int, int, int). RGB color that
            should be blended with note color to make highlight.
            Default: (224, 224, 224, 255)

        Shadows
        =======

        `shadow_positions` is a global setting. All other shadow settings are
        per-voice or global.

        To turn on shadow rendering, ensure that `shadow_positions` is at least
        one tuple long and that at least one voice has a shadow_strength greater
        than 0.

        shadow_strength: float. Controls how strongly `shadow_color` is
            mixed with the current background color to form "shadows".
            Default: 0.6.
        shadow_positions: a list of 2- or 4-tuples of floats. Specifies shadow
            positions relative to notes/lines, in pixels (thus if the
            resolution is changed, shadow_positions should be changed too).
            The advantage of specifying in pixels is that both x and y are in
            the same units (whereas, if they were in, say, pitches and rhythms,
            or proportional to the window size, they would be in different
            units). The disadvantage is that if the resolution is changed, the
            shadow_positions will need to be adjusted too.
            2-tuples are of form (x, y) where x and y apply to both note shadows
                and line shadows
            4-tuples are of form (x, y, shadow_x, shadow_y), where x and y are
                specified separately for notes and shadows.
            Default: []
        shadow_color: tuple of form (int, int, int, int). RGB color that
            should be blended with background color to make shadows.
            Default: (128, 128, 128, 255)
        shadow_scale: float. How much to scale shadows relative to the objects
            they shadow. If there is more than one shadow per note (i.e., if
            `len(shadow_positions) > 1`), then each shadow will be scaled by
            `shadow_scale**n` where n is its position in the list (starting
            from 1). Can be overridden by `shadow_scale_x` or `shadow_scale_y`.
            Default: 1.0
        shadow_scale_x: float. Like shadow_scale, but in the horizontal
            dimension only. Overrides any value specified by `shadow_scale`.
        shadow_scale_y: float. Like shadow_scale, but in the vertical
            dimension only. Overrides any value specified by `shadow_scale`.
        highlight_shadows: boolean. Controls whether shadows are highlighted
            similarly to notes.
            Default: False
        shadow_gradients: boolean. Only useful if `shadow_positions` has length
            greater than 1. If True, then shadow colors will be blended along a
            gradient from closest to the note color (the first shadow in the
            list) to closest to the shadow color (the last shadow in the
            list).
            Default: True
        shadow_gradient_offset: float. When used with shadow gradients, higher
            values will make the first shadow stand out more clearly from the
            note it is shadowing. (The "strength" of the note color added to the
            shadow color is determined by (num_shadows - shadow_i - 1) /
            (num_shadows + shadow_gradient_offset), which for example, for the
            first of four shadows with shadow_gradient_offset = 0, will be 3/4,
            but for the first of four shadows with shadow_gradient_offset = 5,
            will be 3/9.)
            Default: 0.0

        Flutter
        =======

        "Flutter" is constant sinusoidal up-down motion I added to make the
        notes seem more "alive". Each pitch in each channel has a random (but
        constant) flutter size (the vertical distance progressed) and period
        within the ranges defined by the parameters below.

        `flutter_per_voice` is a global setting. All other flutter settings are
        per-voice or global.

        flutter_per_voice: boolean. Global setting only. If False, then each
            pitch has a globally assigned flutter. If True, then flutters are
            assigned to pitches separately for each individual voice. Thus, if
            this is True, unison pitches in different voices will move up and
            down at a slightly different pace from one another, whereas if it
            is False, they will move at the same pace, and thus one voice will
            consistently occlude the voices behind it.
            Default: False.
        max_flutter_size: float. Set upper bound on flutter "size". Measured
            in semitones. As a per-voice setting, only has an effect if
            `flutter_per_voice` is True.
            Default: 0.6
        min_flutter_size: float. Set lower bound on flutter "size". Measured
            in semitones. As a per-voice setting, only has an effect if
            `flutter_per_voice` is True.
            Default: 0.3
        max_flutter_period: float. Set upper bound on flutter period in seconds.
            As a per-voice setting, only has an effect if `flutter_per_voice`
            is True.
            Default: 8.0
        min_flutter_period: float. Set lower bound on flutter period in seconds.
            As a per-voice setting, only has an effect if `flutter_per_voice`
            is True.
            Default: 4.0

        Bounce
        ======

        "Bounce" is scaling or vertical motion that occurs at the attack of a
        note to visually accent the attack. The amount of "bounce" is scaled
        linearly from "now" until `bounce_len` seconds later.

        All bounce settings are per-voice or global.

        bounce_type: string. Either "vertical" (note "bounces" up or down) or
            "scalar" (note is scaled in and out).
            Default: "vertical"
        bounce_size: float.
            If `bounce_type` is "vertical", size of vertical motion in
            semitones.
            If `bounce_type` is "scalar", the "units" are a bit weird because
            the scaling is linear, but I wanted to avoid negative values. Thus
            it works like this: in general, `bounce_size` sets the difference
            between the maximum scalar and the minimum scalar. If `bounce_size`
            is smaller than 2, then this range is centered on 1. E.g., with
            `bounce_size` of 1, the note will be scaled in the range (0.5, 1.5).
            If `bounce_size` is larger than 2, on the other hand, the range will
            be (0, bounce_size), to avoid scaling by negative values. (Perhaps
            a nonlinear function would've been better but that'll have to wait.)
            Default: 0.3
        bounce_period: float. Period of up/down or in/out motion, in seconds.
            Default: 1.0
        bounce_len: float. Length of bounce in seconds.
            Default: 1.0

        Annotations
        ===========

        "brackets", "bracket_settings", and "default_bracket_settings" are
        per-voice. The other settings below are global.

        brackets: a sequence of tuples. This
            setting specifies a series of brackets to draw (e.g., for music
            analytical illustrations). The tuples have 3 mandatory fields and
            3 subsequent optional fields. The tuple fields are as follows:
                - start: either a float or an int. Both start and end must have
                    same type. If a float, specifies
                    the time at which the bracket should start. If an int,
                    specifies the index to the note at which the
                    bracket should start. Zero-indexed. E.g., if the bracket
                    should begin at the first note, the start index is 0.
                - end: either a float or an int. Both start and end must have
                    same type. If a float, specifies
                    the time at which the bracket should start. If an int,
                    specifies the index to the note at which the
                    bracket should end. Zero-indexed. E.g., if the bracket
                    should end at the fifth note, the end index is 4.
                    NB: end should be greater than index.
                    NB also: if an integer index does not exist, the bracket
                    will not be drawn and the script will print a warning.
                - type: a key from the dictionary passed as
                    `bracket_settings` (see below).
                - text: optional str. Specifies what text the bracket
                    should be annotated with. Default: ""
                - loop: optional float. Only implemented if start and end are
                    floats. If passed, then the bracket will be repeated at
                    intervals defined by this float, until the end of the
                    file, or until the time defined by the next parameter.
                - loop_end: optional float. Only implemented if start and end
                    are floats. Defines a time at which the bracket should
                    cease looping; the loop will stop when the next bracket's
                    start time is greater than this value.
            Brackets passed globally will be plotted in all voices, *unless*
            `bracket_settings` is not passed globally, in which case voices that
            do not have `bracket_settings` passed explicitly will not have
            brackets plotted.
        bracket_settings: a dictionary of form (str: dict). The strings are
            labels that are used by `brackets` to fetch the settings to apply
            to each bracket. The dicts define the settings for brackets, as
            follows:
                "color" : a 3-tuple or 4-tuple of ints.
                    Default: (255, 255, 255)
                "above" : bool. If True, the brackets are drawn *above* the
                    specified voice. Otherwise, they are drawn below.
                    Default: False
                "line_width" : float. How wide the line making up the bracket
                    should be. This parameter is passed directly through to R.
                    Default: 5.0
                "height" : float. The vertical size of the bracket, in
                    semitones.
                    Default: 1.0
                "tight" : bool. This parameter is only implemented for brackets
                    whose start and end points are indicated a note indices
                    (i.e., as integers, rather than as floats). If True, the
                    bracket will be placed just below
                    or above the lowest or highest notes that occur during its
                    duration (at a vertical offset defined by "y_offset"
                    below). Otherwise, its vertical placement will be determined
                    by the highest or lowest notes that occur during the entire
                    voice (thus, all brackets with the same "y_offset" in a
                    voice will be at the same vertical position).
                    Default: False
                "y_offset" : float. Sets an offset for the brackets' vertical
                    positions, measured in semitones. Positive values shift the
                    brackets away from the notes. Thus if "above" is True,
                    positive values will shift the brackets upward, whereas if
                    "above" is False, they will shift them downward.
                    Default: 1.0
                "x_offset" : float. Sets an offset for the brackets' horizontal
                    endpoints, measured in seconds. Positive values shift the
                    endpoints inwards, whereas negative values shift them
                    outwards. If you have specified many brackets that are
                    immediately adjacent to one another, you may want to
                    specify a small positive value for this setting, so that
                    the brackets will not elide with one another.
                    Default: 0.0
                "text_size" : float. The font size for the text annotations.
                    This parameter is passed directly through to R.
                    Default: 3.0
                "text_y_offset" : float. Determines the vertical distance of the
                    text annotations from the brackets. Positive values shift
                    the text away from the notes.
                    Default: 0.2
        default_bracket_settings: dict. It is often useful to define a setting
            like "text_y_offset" for all brackets. Any bracket setting for a
            particular bracket type that is not found in `bracket_settings`
            will be fetched from this dict. Only if not found will the
            default values above under `bracket_settings` be applied.
        add_annotations: list of strings. Annotate each frame according to the
            values in this list. Possible values:
                "time" : clock time (intro times are negative)
                "section" : i.e., "intro", "outro", or neither (="main")
            Default: empty.
        annot_color: tuple of form (int, int, int[, int]). Color for
            annotations.
            Default: (255, 255, 255, 255).
        annot_size: float. Sets annot size by scaling the annot with the
            `cex` argument to the R `text` command.
            Default: 1.0
        now_line: boolean. If True, adds a line to each frame indicating "now".
            Default: False.
    """

    midi_fname: typing.Union[  # pylint: disable=unsubscriptable-object
        str, typing.Sequence[str]
    ] = ""
    midi_reset_start_to_0: bool = False
    midi_tracks_to_voices: bool = True
    midi_channels_to_voices: bool = False
    output_dirname: str = DEFAULT_OUTPUT_PATH
    resolution: typing.Tuple[int, int] = (1280, 720)
    _temp_r_dirname: str = DEFAULT_TEMP_R_PATH
    process_video: str = "yes"
    video_fname: str = ""
    audio_fname: str = ""
    clean_up_r_files: bool = True
    clean_up_png_files: bool = True
    tet: int = 12
    seed: int = None
    add_annotations: list = dataclasses.field(default_factory=list)
    annot_color: typing.Tuple[int, int, int] = (255, 255, 255, 255)
    annot_size: float = 1.0
    now_line: bool = False
    _test: bool = False  # append "_test to output filename"

    # lyrics

    lyrics: dict = None
    lyrics_x: float = 0.5
    lyrics_y: float = 0.1
    lyrics_color: float = (255, 255, 255, 255)
    lyrics_size: float = 3.0

    # frame

    frame_len: float = 9
    frame_increment: float = 1 / 30
    frame_position: float = 0.5

    # timing
    intro: float = 1.0
    outro: float = 1.0
    # Use start_time *or* start_bar (and optionally start_beat); if start_bar
    # is nonzero, start_time will be ignored.
    # I believe start_time is in seconds ("clock time").
    start_time: float = 0
    start_bar: int = 0
    start_beat: float = 0

    # If end_time == 0, end time of input midi file is used
    # Use end_time *or* start_bar (and optionally end_beat); if end_bar
    # is nonzero, end_time will be ignored.
    end_time: float = 0
    end_bar: int = 0
    end_beat: float = 0

    # bar_length is only used to interpret start_bar, end_bar, final_bar
    bar_length: float = 0
    scale_notes_from_attack: bool = True

    final_bar: int = 0
    final_beat: float = 0

    voices_to_render: tuple = ()
    voice_order: list = dataclasses.field(default_factory=list)
    voice_order_reverse: bool = False

    voice_settings: dict = dataclasses.field(default_factory=dict)
    duplicate_voice_settings: dict = dataclasses.field(default_factory=dict)
    p_displace: dict = dataclasses.field(default_factory=dict)

    color_palette: typing.Sequence[typing.Tuple[int, int, int, int]] = (
        (41, 120, 142),
        (72, 25, 107),
        (210, 225, 27),
        (34, 167, 132),
        (121, 209, 81),
        (165, 218, 53),
        (30, 152, 138),
        (56, 86, 139),
        (68, 1, 84),
        (83, 197, 103),
        (64, 67, 135),
        (48, 103, 141),
        (35, 136, 141),
        (70, 47, 124),
        (253, 231, 36),
        (53, 183, 120),
    )
    color: typing.Any = None
    color_loop: int = None
    color_loop_var_amount: numbers.Number = 128
    default_note_opacity: int = 255

    connection_lines: bool = True
    con_line_offset_prop: float = 0.0
    con_line_offset_color: tuple = (128, 128, 128, 255)
    max_connection_line_duration: float = 0.25
    max_connection_line_interval: float = None
    no_connection_lines_between_simultaneous_notes: bool = True
    # LONGTERM connection line offsets aren't fully implemented because
    #   they don't take rect scaling into account
    connection_line_start_offset: float = None
    connection_line_end_offset: float = None

    line_start: float = 1.0
    line_end: float = 1.0
    line_start_size: float = 1.0
    line_end_size: float = 1.0
    con_line_width: float = 5

    rectangles: bool = True
    note_start: float = 1
    note_end: float = 1
    note_size: float = 1
    note_width: float = None
    note_height: float = None
    note_start_width: float = 1
    note_end_width: float = 1
    note_start_height: float = 1
    note_end_height: float = 1
    start_scale_function: typing.Callable = lambda x: x
    end_scale_function: typing.Callable = lambda x: x

    highlight_strength: float = 1
    highlight_start: float = 0.1
    highlight_end: float = 0.25
    highlight_color: tuple = (224, 224, 224, 255)

    shadow_strength: float = 0.6
    shadow_positions: typing.Sequence[
        # remove when pylint bug is fixed
        typing.Union[  # pylint: disable=unsubscriptable-object
            typing.Tuple[float, float, float, float], typing.Tuple[float, float]
        ]
    ] = dataclasses.field(default_factory=DEFAULT_SHADOW_POSITIONS)
    shadow_color: tuple = (128, 128, 128, 255)
    shadow_scale: float = 1.0
    shadow_scale_x: float = None
    shadow_scale_y: float = None

    shadow_gradients: bool = True
    shadow_gradient_offset: float = 5
    highlight_shadows: bool = False

    num_channels: int = 1
    channel_proportions: tuple = ()
    chan_assmts: dict = dataclasses.field(default_factory=dict)
    channel_settings: dict = dataclasses.field(default_factory=dict)

    flutter_per_voice: bool = False
    max_flutter_size: float = 0.6
    min_flutter_size: float = 0.3
    max_flutter_period: float = 8.0
    min_flutter_period: float = 4.0

    bounce_type: str = "vertical"
    bounce_size: float = 0.3
    bounce_period: float = 1.0
    bounce_len: float = 1.0

    # If bg_beat_times is empty, or bg_beat_times_length is 0, bg color is
    # constant
    # remove when pylint bug is fixed
    bg_beat_times: typing.Union[  # pylint: disable=unsubscriptable-object
        typing.Sequence[int], typing.Sequence[float]
    ] = (0,)

    bg_beat_times_length: float = 0
    bg_colors: typing.Sequence[typing.Tuple[int, int, int]] = (
        (32, 32, 32, 255),
        (192, 192, 192, 255),
    )
    # If false, bg_colors change abruptly
    bg_color_blend: bool = True
    intro_bg_color: tuple = (0, 0, 0, 255)
    outro_bg_color: tuple = None

    brackets: typing.Sequence[
        typing.Union[  # pylint: disable=unsubscriptable-object
            typing.Tuple[int, int, str],
            typing.Tuple[int, int, str, str],
            typing.Tuple[int, int, str, str, float],
            typing.Tuple[int, int, str, str, float, float],
            typing.Tuple[float, float, str],
            typing.Tuple[float, float, str, str],
            typing.Tuple[float, float, str, str, float],
            typing.Tuple[float, float, str, str, float, float],
        ]
    ] = dataclasses.field(default_factory=list)
    bracket_settings: typing.Dict[str, dict] = None
    default_bracket_settings: dict = dataclasses.field(default_factory=dict)

    _colors = GLOBAL_COLORS + PER_VOICE_COLORS
    _color_lists = GLOBAL_COLOR_LISTS + PER_VOICE_COLOR_LISTS

    def __post_init__(self):
        self.global_parent = self
        # Attributes defined in post_init_helper:
        self.frame_note_start = self.frame_note_end = None
        self.frame_line_start = self.frame_line_end = None
        self.shadow_hl_strength = None
        self.bounce_radius = self.bounce_sin_factor = None
        # End attributes defined in post_init_helper
        self.out_width, self.out_height = self.resolution
        if self.color is not None:
            print("Notice: passing a global value for 'color' has no effect")
            self.color = None
        if not isinstance(self.brackets, list):
            self.brackets = list(self.brackets)

        if not self.midi_fname:
            raise ValueError("no 'midi_fname' keyword argument to Settings()")
        if isinstance(self.midi_fname, str):
            self.midi_fname = (self.midi_fname,)
        if self.seed is not None:
            random.seed(self.seed)
        if self.intro_bg_color is None:
            self.intro_bg_color = self.bg_colors[-1]
        if self.outro_bg_color is None:
            self.outro_bg_color = self.intro_bg_color
        post_init_helper(self)
        if not self.channel_proportions:
            self.channel_proportions = tuple(
                1 for _ in range(self.num_channels)
            )
        else:
            if not len(self.channel_proportions) == self.num_channels:
                raise ValueError(
                    "`len(channel_proportions)` must equal `num_channels`"
                )
        # Add missing channel settings
        for channel_i in range(self.num_channels):
            if channel_i not in self.channel_settings:
                self.channel_settings[
                    channel_i
                ] = DEFAULT_CHANNEL_SETTINGS.copy()
            else:
                for setting in DEFAULT_CHANNEL_SETTINGS:
                    if setting not in self.channel_settings[channel_i]:
                        self.channel_settings[channel_i][
                            setting
                        ] = DEFAULT_CHANNEL_SETTINGS[setting]

        prop_sum = sum(self.channel_proportions)
        self.channel_heights = [
            round(prop / prop_sum * self.out_height)
            for prop in self.channel_proportions
        ]
        self.channel_offsets = [
            sum(self.channel_heights[i + 1 :]) for i in range(self.num_channels)
        ]

        self.temp_r_script_base = os.path.join(
            self._temp_r_dirname, TEMP_R_SCRIPT
        )
        if not self.video_fname:
            self.video_fname = (
                os.path.splitext(os.path.basename(self.midi_fname[0]))[0]
                + ".mp4"
            )
        if self.video_fname == os.path.basename(self.video_fname):
            self.video_fname = os.path.join(
                self.output_dirname, self.video_fname
            )
        self.png_fname_base = os.path.join(
            self.output_dirname,
            os.path.splitext(os.path.basename(self.video_fname))[0],
        )
        if self.png_fname_base[-1].isdigit():
            self.png_fname_base += "_"
        self.png_fnum_digits = 5
        if self._test:
            bits = os.path.splitext(self.video_fname)
            self.video_fname = bits[0] + "_TEST" + bits[1]
        if (
            self.start_bar or self.end_bar or self.final_bar
        ) and not self.bar_length:
            raise ValueError(
                "If any of start_bar, end_bar, or final_bar is "
                "nonzero, bar_length must be nonzero as well."
            )

        self.w_factor = self.out_width / self.frame_len

        if self.note_width is None:
            self.note_width = self.note_size
        if self.note_height is None:
            self.note_height = self.note_size

        if self.shadow_scale_x is None:
            self.shadow_scale_x = self.shadow_scale
        if self.shadow_scale_y is None:
            self.shadow_scale_y = self.shadow_scale

        if self.bracket_settings is not None:
            for name, kwargs in self.bracket_settings.items():
                self.bracket_settings[name] = BracketSettings(
                    self.out_width, **(self.default_bracket_settings | kwargs)
                )

        # The following attributes are only initialized after calling
        # self.update_from_score()

        self.num_voices = self.p_displace_rev = self.voice_assmts = None
        self.final_time = self.bg_clock_times = self.shadows = None
        self.num_shadows = self.max_shadow_x_time = None
        self.min_shadow_x_time = None

    def update_from_score(self, score, tempo_changes):
        self.num_voices = score.num_voices

        self.p_displace_rev = {
            voice: pitch_displacement
            for (pitch_displacement, voices) in self.p_displace.items()
            for voice in voices
        }

        # Get voices_to_render
        if not self.voices_to_render:
            self.voices_to_render = list(range(self.num_voices))

        # Add missing channel assignments
        for voice_i in range(self.num_voices):
            if voice_i not in self.chan_assmts:
                self.chan_assmts[voice_i] = 0

        # Get reverse dictionary for voice assignments
        self.voice_assmts = collections.defaultdict(list)
        for voice_i, chan_i in self.chan_assmts.items():
            self.voice_assmts[chan_i].append(voice_i)

        # Update start_time and end_time if necessary
        if self.start_bar or self.start_beat:
            start_beat = (self.start_bar - 1) * self.bar_length + (
                self.start_beat - 1
            )
            self.start_time = tempo_changes.ctime_from_btime(start_beat)
        if self.end_bar or self.end_beat:
            end_beat = (self.end_bar - 1) * self.bar_length + (
                self.end_beat - 1
            )
            self.end_time = tempo_changes.ctime_from_btime(end_beat)
        elif not self.end_time:
            self.end_time = tempo_changes.ctime_from_btime(
                score.get_total_len()
            )

        # Work out final_time
        if self.final_bar or self.final_beat:
            final_beat = (self.final_bar - 1) * self.bar_length + (
                self.final_beat - 1
            )
            self.final_time = tempo_changes.ctime_from_btime(final_beat)
            if self.final_time > self.end_time:
                self.final_time = self.end_time
        else:
            self.final_time = self.end_time

        # Update voice order
        if not self.voice_order:
            self.voice_order = list(range(self.num_voices))
        else:
            temp = []
            for voice_i in self.voice_order:
                temp.append(voice_i)
                if voice_i in self.duplicate_voice_settings:
                    temp += self.duplicate_voice_settings[voice_i]
            self.voice_order = temp
            for voice_i in range(self.num_voices):
                if voice_i not in self.voice_order:
                    self.voice_order.append(voice_i)

        if self.voice_order_reverse:
            self.voice_order.reverse()

        reversed_duplicate_voice_settings = {}
        voice_init_order = list(range(self.num_voices))
        for src_i, dsts in self.duplicate_voice_settings.items():
            if src_i >= self.num_voices:
                print(
                    f"Warning: voice {src_i} in `duplicate_voice_settings` "
                    "does not exist in score"
                )
                continue
            for dst_i in dsts:
                if dst_i >= self.num_voices:
                    print(
                        f"Warning: voice {dst_i} in `duplicate_voice_settings` "
                        "does not exist in score"
                    )
                    continue
                reversed_duplicate_voice_settings[dst_i] = src_i
                if voice_init_order.index(src_i) > voice_init_order.index(
                    dst_i
                ):
                    voice_init_order.remove(src_i)
                    voice_init_order.insert(0, src_i)

        for voice_i in voice_init_order:
            self.voice_settings[voice_i] = VoiceSettings(
                voice_i,
                self.voice_settings[reversed_duplicate_voice_settings[voice_i]]
                if voice_i in reversed_duplicate_voice_settings
                else self,
                **(
                    self.voice_settings[voice_i]
                    if voice_i in self.voice_settings
                    else {}
                ),
            )

        # get bg_clock_times
        self.bg_clock_times = []
        if (
            self.bg_beat_times
            and self.bg_beat_times_length > 0
            and len(self.bg_colors) >= 2
        ):
            break_out = False
            for i in itertools.count():
                for bg_beat_time in self.bg_beat_times:
                    clock_time = tempo_changes.ctime_from_btime(
                        i * self.bg_beat_times_length + bg_beat_time
                    )
                    if clock_time > self.end_time:
                        break_out = True
                    self.bg_clock_times.append(clock_time)
                    # We put the break here (and not before the append) because
                    # we want to have one extra
                    # bg_time in the list that will never actually be reached,
                    # so that denominators of form (next_bg_time - prev_bg_time)
                    # will never give divide by zero errors.
                    if break_out:
                        break
                if break_out:
                    break

        self.shadows = any(
            v.shadow_strength > 0 for v in self.voice_settings.values()
        )

        self.num_shadows = len(self.shadow_positions)
        self.shadow_positions = [
            ShadowPositions(self.out_width, self.frame_len, *shadow_p)
            for shadow_p in self.shadow_positions
        ]
        self.max_shadow_x_time = max(
            [s.shadow_x for s in self.shadow_positions]
            + [s.cline_shadow_x for s in self.shadow_positions]
            + [
                0,
            ]
        )
        self.min_shadow_x_time = min(
            [s.shadow_x for s in self.shadow_positions]
            + [s.cline_shadow_x for s in self.shadow_positions]
            + [
                0,
            ]
        )
        self.pixel_normalize_attr("con_line_width")
        self.pixel_normalize_attr("lyrics_size")
        self.pixel_normalize_attr("annot_size")

    def pixel_normalize(self, val):
        return val * self.out_width / DEFAULT_PIXEL_WIDTH

    def pixel_normalize_attr(self, attr):
        setattr(self, attr, self.pixel_normalize(getattr(self, attr)))

    def __getitem__(self, key):
        return self.voice_settings[key]

    @property
    def fps(self):
        return 1 / self.frame_increment
