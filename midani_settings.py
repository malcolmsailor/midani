import collections
import dataclasses
import itertools
import math
import os
import typing

# RESOLUTIONS = {
#     "development": (640, 360),
#     "high": (1600, 900),
#     "default": (1280, 720),
# }

DEFAULT_CHANNEL_SETTINGS = {
    "l_pitch_padding": 1,
    "h_pitch_padding": 1,
    "bg_colors": (32, 32, 32),
}

# TODO padding as a proportion of channel (rather than in pitches)

TEMP_R_SCRIPT = "midani{:06d}.R"

DEFAULT_SHADOW_POSITIONS = lambda: [(10, -10)]

ShadowPositions = collections.namedtuple(
    "ShadowPositions",
    ["shadow_x", "shadow_y", "cline_shadow_x", "cline_shadow_y"],
    defaults=[None, None],
)


@dataclasses.dataclass
class Settings:
    """Settings for midi animation plotting.

    Can be indexed like a list or a tuple to get voice-specific settings. E.g.,
    settings[2] will get voice-specific settings for voice with index 2.

    Some settings are omitted from the description of keyword arguments below
    as they are unlikely to be of interest to the user (they are in a sense
    "private" to the script). # TODO maybe these should have a leading underscore?

    When these settings contain terms like "start" and "end", these refer to
    positions *on each frame*. E.g., `note_start` is how far from the left side
    of each frame notes should begin. But notes are moving to the left, so this
    is actually the last moment at which the note will occur---so from another
    perspective, it should be "note_end."

    Args:
        midifname: str. Path to input midi file to animate.

    Keyword args:
        output_dirname: str. path to folder where output images will be created.
            If a relative path, will be created relative to the script
            directory. If the path does not exist, it will be created.
            Default: "midani_output"
        resolution: tuple of form (int, int). Resolution of output frames.
            Default (1280, 720)
        process_video: str. Possible values:
            "yes": (Default) makes .mp4 video file using OpenCV
            "no": doesn't make video file.
            "only": makes .mp4 video file using OpenCV and skips the rest of the
                script. (Note: in this case, the number of frames will be
                inferred from the number of files that match the png filename
                in `output_dirname`.)
        video_fname: str. Path to output video file. If not passed, the video
            will be written in `output_dirname` with the same basename as
            `midifname`. Has no effect if `process_video` == "no".
        clean_up_r_files: bool. If False, the R scripts output by this script
            will not be deleted (and so can be inspected).
            Default: True.
        tet: int. Set temperament.
            Default: 12 (for 12-tone equal temperament.)

        debugging
        =========

        add_annotations: list of strings. Annotate each frame according to the
            values in this list. Possible values:
                "time"
            Default: empty.
        annot_color: tuple of form (int, int, int). Color for annotations.
            Default: (255, 255, 255).
        now_line: boolean. If True, adds a line to each frame indicating "now".
            Default: False.

        frame
        ======

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

        timing
        ======

        intro: float. Length of time in seconds that should precede `start_time`
            Default: 5.0
        outro: float. Length of time in seconds that should follow `end_time`
            Default: 5.0
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
            Default: 0
        start_beat: float. Notes before this beat in the input midi file will be
            ignored (not drawn). Can be used in combination with `start_bar`
            (e.g., to indicate "4th bar, 3rd beat") or on its own (which could
            be useful if the time signature changes frequently).
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
            Default: 0
        end_beat: float. Notes after this beat in the input midi file will be
            ignored (not drawn). Can be used in combination with `end_bar`
            (e.g., to indicate "4th bar, 3rd beat") or on its own (which could
            be useful if the time signature changes frequently).
            Default: 0
        bar_length: float. (Only) used to interpret `start_bar`, `end_bar`,
            and/or `final_bar`. If any of these latter are nonzero, it will
            raise a ValueError not to pass a nonzero value of this setting.

        scale_notes_from_attack: bool. If True, then notes and lines are scaled based
            on their attack time. Otherwise, they are scaled based on the
            midpoint between their attack and their release.

        voice settings
        ==============

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

        connection lines
        ================

        connection_lines: boolean. If True, "connection lines" are drawn between
            adjacent notes on the same track (subject to certain conditions,
            controlled by the subsequent keyword arguments). Note that this sets
            a default that can be overridden on a per-voice basis. # TODO document
            Default: True
        max_connection_line_distance: float. Maximum time interval in seconds
            between end of one note and beginning of next for which a
            connection line will be drawn.
            Default: 0.25
        max_connection_line_interval: float. Maximum pitch interval (in
            temperament as defined by `tet`) between notes for which a
            connection line will be drawn.
            By default, set to value of `tet` (i.e., one octave).
        no_connection_lines_between_simultaneous_notes: boolean. If True, then
            connection lines are not drawn between simultaneous notes in the
            same part. # TODO improve drawing of connection lines in this sort of cases?
            Default: True
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
        con_line_width: float. Width of connection lines at moment `now`. If
            `line_start_size` or `line_end_size` != 1, then the scaling of the
            lines will gradually change until `now`. # TODO write more clearly?
        line_start_size: float. Amount by which `con_line_width` should be
            scaled at `line_start`.
            Default: 1.0
        line_end_size: float. Amount by which `con_line_width` should be
            scaled at `line_end`.
            Default: 1.0


        notes (or "rectangles")
        =======================
        rectangles: boolean. If True, a "rectangle" (the usual piano-roll
            representation) is drawn for each note. Note that this sets
            a default that can be overridden on a per-voice basis. # TODO document
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
        default_note_size: float. Factor by which notes should be scaled at
            moment `now`. The base height of a note is 1 semitone, and the base
            width is its duration, so if > 1, rectangles will overlap each
            other, whereas if it is < 1, they will have extra spacing. If
            either `default_note_x_size` or `default_note_y_size` are nonzero,
            this argument is ignored in the width or height dimension,
            respectively (or both). Note that this argument, as well as all
            other note size arguments below, sets a default that can be
            overridden on a per-voice basis.
            Default: 1.
        default_note_x_size: float. Overrides `default_note_size` in x
            dimension.
        default_note_y_size: float. Overrides `default_note_size` in y
            dimension.
        note_start_x_size: float. Amount by which `default_note_size` should be
            scaled horizontally at `line_start`.
            Default: 1.0
        note_start_y_size: float. Amount by which `default_note_size` should be
            scaled vertically at `line_start`.
            Default: 1.0
        note_end_x_size: float. Amount by which `default_note_size` should be
            scaled horizontally at `line_end`.
            Default: 1.0
        note_end_y_size: float. Amount by which `default_note_size` should be
            scaled vertically at `line_end`.
            Default: 1.0

        highlight
        =========
        highlight_strength: float. Controls how strongly `highlight_color` is
            mixed with the current note color at moment `now`.
            Default: 1.0
        highlight_start: float. Time in seconds when highlight should begin.
            The amount of `highlight_color` blended with the current note
            color will scale linearly from 0 beginning at this moment up to
            `highlight_strength` at `now`.
            Default: 0.1
        highlight_end: float. Time in seconds when highlight should emd.
            The amount of `highlight_color` blended with the current note
            color will scale linearly from `highlight_strength` at `now` down
            to 0 at this moment.
            Default: 0.25
        highlight_color: tuple of form (int, int, int). RGB color that should
            be blended with note color to make highlight.
            Default: (224, 224, 224)

        shadows
        =======
        shadow_strength: float. Controls how strongly `shadow_color` is mixed
            with the current background color to form "shadows".
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
            Default: [(10, -10)]
        highlight_shadows: boolean. Controls whether shadows are highlighted
            similarly to notes.
            Default: False
        shadow_scale: float. How much to scale shadows relative to the objects
            they shadow.
            # TODO make this apply to lines
            Default: 1.0



    Attributes:
        attribute_name: attribute_description

    Methods:
        method_name: method_description
    """

    midifname: str  # doc
    output_dirname: str = "midani_output"  # TODO better default path? # doc
    resolution: typing.Tuple[int, int] = (1280, 720)  # doc
    # NB If _temp_r_dirname contains spaces, it seems R will not run correctly
    _temp_r_dirname: str = "/Users/Malcolm/tmp/temp_r_files"  # TODO better path
    process_video: str = "yes"  # doc
    video_fname: str = ""  # doc
    clean_up_r_files: bool = True  # doc
    tet: int = 12  # doc
    add_annotations: list = dataclasses.field(default_factory=list)  # doc
    annot_color: typing.Tuple[int, int, int] = (255, 255, 255)  # doc
    now_line: bool = False  # doc

    # frame

    frame_len: float = 9  # doc
    frame_increment: float = 1 / 30  # doc
    frame_position: float = 0.5  # doc

    # timing
    intro: float = 5  # doc
    outro: float = 5  # doc
    # Use start_time *or* start_bar (and optionally start_beat); if start_bar
    # is nonzero, start_time will be ignored.
    # I believe start_time is in seconds ("clock time").
    start_time: float = 0  # doc
    start_bar: int = 0  # doc
    start_beat: float = 0  # doc

    # If end_time == 0, end time of input midi file is used
    # Use end_time *or* start_bar (and optionally end_beat); if end_bar
    # is nonzero, end_time will be ignored.
    end_time: float = 0  # doc
    end_bar: int = 0  # doc
    end_beat: float = 0  # doc

    # bar_length is only used to interpret start_bar, end_bar, final_bar
    bar_length: float = 0  # doc
    scale_notes_from_attack: bool = True  # doc

    # TODO check that p_displace are consistent, e.g., something
    # like {4: (6), 3: (6)} should raise an error because 6 is to be displaced
    # by both 4 and 3 semitones
    p_displace: dict = dataclasses.field(default_factory=dict)

    # TODO why is there no "final_time" analogous to "start_time" and "end_time?"
    # Final time specifies the point after which the background fades out
    # QUESTION should the approach to the end be more like the approach to the
    # beginning? (specify an outro length in seconds?)
    # What happens if final_bar etc. is unspecified?
    final_bar: int = 0  # TODO doc
    final_beat: float = 0  # TODO doc

    voices_to_render: tuple = ()  # doc
    voice_order: list = dataclasses.field(default_factory=list)  # doc
    voice_order_reverse: bool = False  # doc

    # TEST connection_line parameters
    connection_lines: bool = True  # doc
    max_connection_line_distance: float = 0.25  # doc
    max_connection_line_interval: float = None  # doc
    no_connection_lines_between_simultaneous_notes: bool = True  # doc

    line_start: float = 1.0  # doc
    line_end: float = 1.0  # doc
    line_start_size: float = 1.0  # doc
    line_end_size: float = 1.0  # doc
    con_line_width: float = 5  # doc

    rectangles: bool = True  # doc
    note_start: float = 1  # doc
    note_end: float = 1  # doc
    default_note_size: float = 1  # doc
    default_note_x_size: float = 0  # doc
    default_note_y_size: float = 0  # doc
    note_start_x_size: float = 1  # doc
    note_end_x_size: float = 1  # doc
    note_start_y_size: float = 1  # doc
    note_end_y_size: float = 1  # doc

    highlight_strength: float = 1  # doc
    highlight_start: float = 0.1  # doc
    highlight_end: float = 0.25  # doc
    highlight_color: tuple = (224, 224, 224)  # doc

    shadow_strength: float = 0.6  # doc
    shadow_positions: typing.Sequence[
        typing.Union[
            typing.Tuple[float, float, float, float], typing.Tuple[float, float]
        ]
    ] = dataclasses.field(
        default_factory=DEFAULT_SHADOW_POSITIONS
    )  # doc
    default_shadow_color: tuple = (0, 0, 0)
    shadow_scale: float = 1.0

    # TODO what do shadow_gradients do?
    shadow_gradients: bool = True
    shadow_gradient_offset: float = 5
    highlight_shadows: bool = False

    # TODO doc
    shadows_over_clines = True

    # TODO what exactly does close_shadows do?
    # close_shadows: bool = True  # TODO delete this attribute?

    duplicate_voice_settings: dict = dataclasses.field(default_factory=dict)

    num_channels: int = 1
    channel_proportions: tuple = ()
    chan_assmts: dict = dataclasses.field(default_factory=dict)

    channel_settings: dict = dataclasses.field(default_factory=dict)

    start_scale_function: typing.Callable = lambda x: x
    end_scale_function: typing.Callable = lambda x: x

    # Only implemented flutter_type is "vertical" so commented-out for now
    # flutter_type: str = "vertical"
    max_flutter_size: float = 1 / 4
    min_flutter_size: float = 1 / 4
    # flutter period is in seconds
    max_flutter_period: float = 12
    min_flutter_period: float = 4

    # bounce_type can be
    #   - "vertical" (note bounces up and down)
    #   - "scalar" (size of note is scaled in and out)
    bounce_type: str = "vertical"
    # bounce size in semitones
    bounce_size: float = 0
    # bounce period in seconds [in original script, bounce_period was in beats]
    bounce_period: float = 1
    # bounce length in seconds [in original script, bounce_period was in beats]
    bounce_len: float = 1 / 4
    # in radians
    bounce_sin_factor: float = 2 * math.pi
    voice_settings: dict = dataclasses.field(default_factory=dict)

    # TODO clean up
    # rectangles: list = dataclasses.field(default_factory=DEFAULT_RECTANGLE_LIST)

    color_palette: typing.Sequence[typing.Tuple[int, int, int]] = (
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

    # If bg_beat_times is empty, or bg_beat_times_modulo is 0, bg color is
    # constant
    bg_beat_times: typing.Union[
        typing.Sequence[int], typing.Sequence[float]
    ] = (0,)
    bg_beat_times_modulo: int = 8
    bg_colors: typing.Sequence[typing.Tuple[int, int, int]] = (
        (32, 32, 32),
        (192, 192, 192),
    )
    # If false, bg_colors change abruptly
    bg_color_gradients: bool = True
    start_bg_color: tuple = (192, 32, 32)
    end_bg_color: tuple = (32, 192, 32)

    def __post_init__(self):
        if not self.channel_proportions:
            self.channel_proportions = tuple(
                1 for _ in range(self.num_channels)
            )
        else:
            assert (
                len(self.channel_proportions) == self.num_channels
            ), "len(self.channel_proportions) != self.num_channels"
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
            prop / prop_sum for prop in self.channel_proportions
        ]
        self.channel_offsets = [
            sum(self.channel_heights[i + 1 :]) for i in range(self.num_channels)
        ]

        self.default_voice_settings = {
            "connection_lines": self.connection_lines,
            "rectangles": self.rectangles,
            "size": self.default_note_size,
            "size_x": self.default_note_x_size,
            "size_y": self.default_note_y_size,
            "color": None,  # choose at random from colormap
            "shadow_color": self.default_shadow_color,
            "shadow_strength": self.shadow_strength,
        }

        # Get missing voice_settings
        for voice_i in self.duplicate_voice_settings:
            if voice_i not in self.voice_settings:
                voice_settings[voice_i] = self.default_voice_params.copy()

        # Misc processing

        self.shadow_hl_strength = (
            self.highlight_strength * self.highlight_shadows
        )

        # self.rectangles.reverse()
        self.note_start = self.note_start * self.frame_len * self.frame_position
        self.note_end = (
            self.note_end * self.frame_len * (1 - self.frame_position)
        )

        self.line_start = self.line_start * self.frame_len * self.frame_position
        self.line_end = (
            self.line_end * self.frame_len * (1 - self.frame_position)
        )
        self._max_end = max(self.note_end, self.line_end)
        self._max_start = max(self.note_start, self.line_start)
        if not os.path.isabs(self._temp_r_dirname):
            self._temp_r_dirname = os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                self._temp_r_dirname,
            )
        self.temp_r_script_base = os.path.join(
            self._temp_r_dirname, TEMP_R_SCRIPT
        )
        if not os.path.isabs(self.output_dirname):
            self.output_dirname = os.path.join(
                os.path.dirname(os.path.realpath(__file__)), self.output_dirname
            )
        self.png_fname_base = os.path.join(
            self.output_dirname,
            os.path.splitext(os.path.basename(self.midifname))[0],
        )
        self._png_fnum_digits = 5
        if not self.video_fname:
            self.video_fname = os.path.join(
                self.output_dirname,
                os.path.splitext(os.path.basename(self.midifname))[0] + ".mp4",
            )
        if (
            self.start_bar or self.end_bar or self.final_bar
        ) and not self.bar_length:
            raise ValueError(
                "If any of start_bar, end_bar, or final_bar is "
                "nonzero, bar_length must be nonzero as well."
            )
        self.out_width, self.out_height = self.resolution

        if self.max_connection_line_interval is None:
            self.max_connection_line_interval = self.tet

    def update_from_score(self, score, tempo_changes):
        self.num_voices = score.num_voices

        self.p_displace_rev = {
            voice: pitch_displacement
            for (pitch_displacement, voices) in self.p_displace.items()
            for voice in voices
        }

        # Get voices_to_render
        if not self.voices_to_render:
            self.voices_to_render = [i for i in range(self.num_voices)]

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
            self.voice_order = [i for i in range(self.num_voices)]
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
        # Original script contains the following lines (where "a" is the return
        # value from midi_to_internal_data). Not sure why they were necessary,
        # or if they may be again.
        # temp_voice_order = []
        # for i in voice_order:
        #     if i <= len(a) - 1:
        #         temp_voice_order.append(i)
        # voice_order = temp_voice_order
        if self.voice_order_reverse:
            self.voice_order.reverse()

        for src_i, dsts in self.duplicate_voice_settings.items():
            for dst_i in dsts:
                if dst_i not in self.voice_settings:
                    self.voice_settings[dst_i] = {}
                for setting in self.voice_settings[src_i]:
                    if setting not in self.voice_settings[dst_i]:
                        self.voice_settings[dst_i][
                            setting
                        ] = self.voice_settings[src_i][setting]

        for voice_i in range(self.num_voices):
            if voice_i not in self.voice_settings:
                self.voice_settings[
                    voice_i
                ] = self.default_voice_settings.copy()
            else:
                for setting in self.default_voice_settings:
                    if setting not in self.voice_settings[voice_i]:
                        self.voice_settings[voice_i][
                            setting
                        ] = self.default_voice_settings[setting]
            if self.voice_settings[voice_i]["color"] is None:
                self.voice_settings[voice_i]["color"] = self.color_palette[
                    voice_i % len(self.color_palette)
                ]
            for size_axis in ("size_x", "size_y"):
                # if size_axis not in self.voice_settings[voice_i]:
                if not self.voice_settings[voice_i][size_axis]:
                    self.voice_settings[voice_i][
                        size_axis
                    ] = self.voice_settings[voice_i]["size"]
            del self.voice_settings[voice_i]["size"]

        # get bg_clock_times
        # TODO test
        self.bg_clock_times = []
        if self.bg_beat_times and self.bg_beat_times_modulo > 0:
            break_out = False
            for i in itertools.count():
                for bg_beat_time in self.bg_beat_times:
                    clock_time = tempo_changes.ctime_from_btime(
                        i * self.bg_beat_times_modulo + bg_beat_time
                    )
                    if clock_time > self.end_time:
                        break_out = True
                        break
                    self.bg_clock_times.append(clock_time)
                if break_out:
                    break
        # TODO original script has these lines, do I need a version of them?
        # if not bg_times or (len(bg_times) == 1 and bg_times[0] == final_time):
        #     bg_times.insert(0, start_time)
        self.w_factor = self.out_width / self.frame_len
        self.num_shadows = len(self.shadow_positions)
        self.shadow_positions = [
            ShadowPositions(
                shadow_x=s[0] / self.w_factor,
                shadow_y=s[1] / self.out_height,
                cline_shadow_x=(s[2] if len(s) > 2 else s[0]) / self.w_factor,
                cline_shadow_y=(s[3] if len(s) > 3 else s[1]) / self.out_height,
            )
            for s in self.shadow_positions
        ]
        self.max_shadow_x_time = max(
            [s.shadow_x for s in self.shadow_positions]
            + [s.cline_shadow_x for s in self.shadow_positions]
            + [0,]
        )
        self.min_shadow_x_time = min(
            [s.shadow_x for s in self.shadow_positions]
            + [s.cline_shadow_x for s in self.shadow_positions]
            + [0,]
        )

    def __getitem__(self, key):
        return self.voice_settings[key]

    @property
    def fps(self):
        return 1 / self.window_increment
