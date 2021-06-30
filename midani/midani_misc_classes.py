"""Provides a number of classes used internally by midani.
"""

import dataclasses
import functools
import math
import random
import typing

from . import midani_colors


@dataclasses.dataclass
class Note:  # pylint: disable=missing-class-docstring
    pitch: int
    start: float
    end: float

    def __post_init__(self):
        self.dur = self.end - self.start
        self.mid = self.start + self.dur / 2


@dataclasses.dataclass
class RectTuple:
    """Stores data used to plot rectangles."""

    note: Note
    scale_x_factor: float
    scale_y_factor: float
    flutter: float
    color: typing.Tuple[int, int, int]
    highlight_factor: float

    @functools.cached_property
    def pitch(self):
        return self.note.pitch + self.flutter


@dataclasses.dataclass
class LineTuple:
    """Stores data used to plot lines."""

    note: Note
    scale_factor: float
    flutter: float
    color: typing.Tuple[int, int, int]
    highlight_factor: float

    @functools.cached_property
    def pitch(self):
        return self.note.pitch + self.flutter


class PitchFlutter:
    """Calculates 'flutter' according to provided parameters."""

    def __init__(
        self,
        max_flutter_size,
        min_flutter_size,
        max_flutter_period,
        min_flutter_period,
    ):
        self.flutter_size = (
            random.random() * (max_flutter_size - min_flutter_size)
            + min_flutter_size
        )
        self.flutter_period = (
            random.random() * (max_flutter_period - min_flutter_period)
            + min_flutter_period
        )
        self.flutter_offset = random.random() * self.flutter_period
        self.flutter_sin_factor = (2 * math.pi) / self.flutter_period

    def __call__(self, now):
        return (
            math.sin((now + self.flutter_offset) * self.flutter_sin_factor)
            * self.flutter_size
        )


class Window:
    """A class that keeps track of frame position and background color."""

    def __init__(self, settings):
        self.frame_len = settings.frame_len
        self.frame_position = settings.frame_position
        self.start_time = settings.start_time
        self.end_time = settings.end_time
        self.stop_time = settings.end_time + settings.outro
        self.end_bg_time = min(settings.end_time, settings.final_time)
        self.intro = settings.intro
        self.outro = self.stop_time - self.end_bg_time
        self.bg_colors = settings.bg_colors
        self.intro_bg_color = settings.intro_bg_color
        self.outro_bg_color = settings.outro_bg_color
        self.bg_color_blend = settings.bg_color_blend
        self.bg_times = settings.bg_clock_times
        self.bg_time_i = -1
        self.bg_color_constant = not self.bg_times
        self.outro_has_begun = False
        self._top = settings.out_height
        # The next lines are part of an abortive attempt to express
        # x coordinates in pixels, which I foolishly started before
        # committing other changes...
        # self._pixel_width = settings.out_width
        # self._left_pixel_width = int(self._pixel_width * self.frame_position)
        # self._right_pixel_width = self._pixel_width - self._left_pixel_width
        # The following attributes are only initialized later
        self.last_now = self.next_bg_time = self.prev_bg_time = None
        self._now = self._start = self._end = None

    def _update_bg_times(self):
        try:
            if self._now < self.last_now:
                raise ValueError
        except TypeError:
            pass
        self.last_now = self._now
        try:
            while self._now >= self.bg_times[self.bg_time_i + 1]:
                self.bg_time_i += 1
        except IndexError:
            self.next_bg_time = self.end_bg_time
        else:
            self.next_bg_time = self.bg_times[self.bg_time_i + 1]
        if self.bg_time_i < 0:
            self.prev_bg_time = self.start_time
        else:
            self.prev_bg_time = self.bg_times[self.bg_time_i]

    @property
    def bg_color(self):
        """Meant to be called with now in montonically ascending sequence,
        raises a value error otherwise."""
        if self.bg_color_constant:
            return self.bg_colors[0]
        # "between start and end"
        if self.in_main:
            self._update_bg_times()
            prev_bg_color = self.bg_colors[self.bg_time_i % len(self.bg_colors)]
            if not self.bg_color_blend:
                return prev_bg_color
            bg_prop = (self._now - self.prev_bg_time) / (
                self.next_bg_time - self.prev_bg_time
            )
            next_bg_color = self.bg_colors[
                (self.bg_time_i + 1) % len(self.bg_colors)
            ]
        # "before start"
        elif self.in_intro:
            prev_bg_color = self.intro_bg_color
            if not self.bg_color_blend:
                return prev_bg_color
            if self.bg_times[0] > 0:
                next_bg_color = self.bg_colors[-1]
            else:
                next_bg_color = self.bg_colors[0]
            # In first version of the script, this has a considerably more
            # complicated expression that I'm uncertain of the motivation for
            bg_prop = 1 - (self.start_time - self._now) / self.intro
        # "after end"
        elif self.in_outro:
            self._update_bg_times()
            self.outro_has_begun = True
            next_bg_color = self.outro_bg_color
            if not self.bg_color_blend:
                return next_bg_color
            prev_bg_color = self._last_bg_color_before_outro
            bg_prop = (self._now - self.end_bg_time) / self.outro
        return midani_colors.blend_colors(
            prev_bg_color,
            next_bg_color,
            bg_prop,
        )

    @functools.cached_property
    def _last_bg_color_before_outro(self):
        """Raises an error if called when self.outro_has_begun is False."""
        if self.outro_has_begun is False:
            raise ValueError(
                "`_last_bg_color_before_outro` should only be called after "
                "outro has begun"
            )

        prev_bg_color = self.bg_colors[self.bg_time_i % len(self.bg_colors)]
        next_bg_color = self.bg_colors[
            (self.bg_time_i + 1) % len(self.bg_colors)
        ]
        bg_prop = (self.end_bg_time - self.prev_bg_time) / (
            self.next_bg_time - self.prev_bg_time
        )
        return midani_colors.blend_colors(prev_bg_color, next_bg_color, bg_prop)

    def get_first_now(self):
        if self.intro >= 0:
            return -self.intro + self.start_time
        return (
            -math.floor(self.frame_len * self.frame_position) + self.start_time
        )

    def in_range(self, time):
        return time <= self.stop_time

    def update(self, now):
        self._now = now
        self._start = now - self.frame_len * self.frame_position
        self._end = now + self.frame_len * (1 - self.frame_position)
        # The next lines are part of an abortive attempt to express
        # x coordinates in pixels, which I foolishly started before
        # committing other changes...
        # self._pixel_now = round(now / self.frame_len * self._pixel_width)
        # self._pixel_start = self._pixel_now - self._left_pixel_width
        # self._pixel_end = self._pixel_now + self._right_pixel_width

    @property
    def start(self):  # pylint: disable=missing-docstring
        return self._start

    @property
    def end(self):  # pylint: disable=missing-docstring
        return self._end

    # The next lines are part of an abortive attempt to express
    # x coordinates in pixels, which I foolishly started before
    # committing other changes...
    # @property
    # def pixel_start(self):  # pylint: disable=missing-docstring
    #     return self._pixel_start
    #
    # @property
    # def pixel_end(self):  # pylint: disable=missing-docstring
    #     return self._pixel_end

    @property
    def bottom(self):
        # For now, at least, this is always just 0
        return 0

    @property
    def top(self):
        # For now, at least, this is always just the height of the frame in
        # pixels, stored in _top
        return self._top

    @property
    def range(self):
        return 1

    @property
    def now(self):  # pylint: disable=missing-docstring
        return self._now

    @property
    def in_main(self):
        return self.start_time <= self._now <= self.end_bg_time

    @property
    def in_intro(self):
        return self._now < self.start_time

    @property
    def in_outro(self):
        return self._now > self.end_bg_time

    def y_position(self, y):
        """Given y between 0 and 1, returns its coordinates in pixels.

        *Note* y coordinates should be taken from Channel.y_position
        """
        return round(y * self._top)

    # The next lines are part of an abortive attempt to express
    # x coordinates in pixels, which I foolishly started before
    # committing other changes...
    # def x_width(self, x):
    #     return round(x * self._pixel_width / self.frame_len)
    #
    # def x_position(self, x):
    #     return round(x * self._pixel_width / self.frame_len)


class PitchRange:
    """Used by child classes below to determine where pitches lie in range."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._l_pitch = None
        self._h_pitch = None
        self._pitch_range = None

    def update_from_pitch(self, pitch):
        if self._l_pitch is None or pitch < self._l_pitch:
            self._l_pitch = pitch
        if self._h_pitch is None or pitch > self._h_pitch:
            self._h_pitch = pitch
        self._update_pitch_range()

    @property
    def pitch_range(self):  # pylint: disable=missing-docstring
        return self._pitch_range

    def _update_pitch_range(self):
        try:
            self._pitch_range = self._h_pitch - self._l_pitch
        except TypeError:
            self._pitch_range = 1
        else:
            if self._pitch_range == 0:
                self._pitch_range = 1

    @property
    def l_pitch(self):  # pylint: disable=missing-docstring
        return self._l_pitch

    @l_pitch.setter
    def l_pitch(self, pitch):
        self._l_pitch = pitch
        self._update_pitch_range()

    @property
    def h_pitch(self):  # pylint: disable=missing-docstring
        return self._h_pitch

    @h_pitch.setter
    def h_pitch(self, pitch):
        self._h_pitch = pitch
        self._update_pitch_range()


class VoiceList(PitchRange, list):
    """A list/PitchRange object.

    The only implemented method for adding objects is append().
    """

    def append(self, note):
        super().append(note)
        self.update_from_pitch(note.pitch)

    def insert(self, *args, **kwargs):
        raise NotImplementedError

    def extend(self, *args, **kwargs):
        raise NotImplementedError


class Channel(PitchRange):
    """Represents a horizontal 'channel' within which notes can be plotted."""

    def __init__(self, channel_i, settings):
        super().__init__()
        self.l_padding = settings.channel_settings[channel_i]["l_padding"]
        self.h_padding = settings.channel_settings[channel_i]["h_padding"]
        self.non_padding = 1 - self.l_padding - self.h_padding
        self.height = settings.channel_heights[channel_i]
        self.offset = settings.channel_offsets[channel_i]
        self.h_factor = settings.out_height / self.height

    def proportion(self, pitch):
        return round(
            (
                (pitch - self.l_pitch) / self.pitch_range * self.non_padding
                + self.l_padding
            )
            * self.height
        )

    @property
    def note_height(self):  # pylint: disable=missing-docstring
        return 1 / self.pitch_range * self.height * self.non_padding

    def y_position(self, pitch):
        """Returns the y position of a pitch in the frame, in pixels."""
        return self.proportion(pitch) + self.offset

    def pixel_height(self, height):
        return round(
            (self.proportion(self.l_pitch + 1) - self.proportion(self.l_pitch))
            * height
        )


class PitchTable(PitchRange, list):
    """Reads a Score and then builds a "pitch table" for use in plotting.

    Note that voices in this list are in order "voice_order" so if we use
    the indices in "voice_order" to get items from it, we will fetch the wrong
    items.
    """

    def __init__(self, score, settings, tempo_changes, *args, **kwargs):
        super().__init__()
        self.settings = settings
        self.equal_start_xy_size = tuple(
            settings[voice_i].note_start_width
            == settings[voice_i].note_start_height
            for voice_i in range(settings.num_voices)
        )
        self.equal_end_xy_size = tuple(
            settings[voice_i].note_end_width
            == settings[voice_i].note_end_height
            for voice_i in range(settings.num_voices)
        )
        self.voice_ranges = []
        self.l_pitch = None
        self.h_pitch = None
        self.channels = {
            chan_i: Channel(chan_i, settings)
            for chan_i in range(settings.num_channels)
        }
        self.pitch_flutters = {}
        for voice_i in settings.voice_order:
            voice = score.voices[voice_i]
            chan_assmt = settings.chan_assmts[voice_i]
            pitch_displacement = (
                settings.p_displace_rev[voice_i]
                if voice_i in settings.p_displace_rev
                else 0
            )
            voice_list = VoiceList()
            self.append(voice_list)
            if voice_i not in settings.voices_to_render:
                continue
            for note in voice:
                attack_ctime = tempo_changes.ctime_from_btime(note.attack_time)
                end_dur_ctime = tempo_changes.ctime_from_btime(
                    note.attack_time + note.dur
                )
                pitch = note.pitch + pitch_displacement
                voice_list.append(Note(pitch, attack_ctime, end_dur_ctime))

            if voice_list:  # voice is not empty
                self.channels[chan_assmt].update_from_pitch(voice_list.l_pitch)
                self.channels[chan_assmt].update_from_pitch(voice_list.h_pitch)

            if settings.flutter_per_voice:
                voice_flutters = {}
                if voice_list:
                    for pitch in range(
                        voice_list.l_pitch, voice_list.h_pitch + 1
                    ):
                        voice_flutters[pitch] = PitchFlutter(
                            settings[voice_i].max_flutter_size,
                            settings[voice_i].min_flutter_size,
                            settings[voice_i].max_flutter_period,
                            settings[voice_i].min_flutter_period,
                        )
                self.pitch_flutters[voice_i] = voice_flutters
        for channel in self.channels.values():
            if channel.l_pitch is not None:
                self.update_from_pitch(channel.l_pitch)
                self.update_from_pitch(channel.h_pitch)

        # TODO implement or delete
        # for voice_i, voice in enumerate(self):
        #     if "take_l_pitch_from_voice" in settings.voice_settings[voice_i]:
        #         voice.l_pitch = self[
        #             settings.voice_settings[voice_i]["take_l_pitch_from_voice"]
        #         ].l_pitch
        #     if "take_h_pitch_from_voice" in settings.voice_settings[voice_i]:
        #         voice.h_pitch = self[
        #             settings.voice_settings[voice_i]["take_h_pitch_from_voice"]
        #         ].h_pitch
        # Get pitch_flutters

        if not settings.flutter_per_voice:
            for channel_i, voice_indices in settings.voice_assmts.items():
                channel_flutters = {}
                try:
                    pitch_r = range(
                        self.channels[channel_i].l_pitch,
                        self.channels[channel_i].h_pitch + 1,
                    )
                except TypeError:  # channel is empty
                    pass
                else:
                    for pitch in pitch_r:
                        channel_flutters[pitch] = PitchFlutter(
                            settings.max_flutter_size,
                            settings.min_flutter_size,
                            settings.max_flutter_period,
                            settings.min_flutter_period,
                        )
                for voice_i in voice_indices:
                    self.pitch_flutters[voice_i] = channel_flutters

    @staticmethod
    def _get_scale_factor(
        time, end_or_start, start_or_end_size, voice_size, scale_func
    ):
        return max(
            0,
            (
                (1 - scale_func(time / end_or_start)) * (1 - start_or_end_size)
                + start_or_end_size
            )
            * voice_size,
        )

    def _scale_x_factor(self, t_until, voice_i):
        if t_until >= 0:
            return self._get_scale_factor(
                t_until,
                self.settings[voice_i].frame_note_end,
                self.settings[voice_i].note_end_width,
                self.settings[voice_i].note_width,
                self.settings[voice_i].end_scale_function,
            )
        return self._get_scale_factor(
            -t_until,
            self.settings[voice_i].frame_note_start,
            self.settings[voice_i].note_start_width,
            self.settings[voice_i].note_width,
            self.settings[voice_i].start_scale_function,
        )

    def _scale_y_factor(self, t_until, voice_i):
        if t_until >= 0:
            return self._get_scale_factor(
                t_until,
                self.settings[voice_i].frame_note_end,
                self.settings[voice_i].note_end_height,
                self.settings[voice_i].note_height,
                self.settings[voice_i].end_scale_function,
            )
        return self._get_scale_factor(
            -t_until,
            self.settings[voice_i].frame_note_start,
            self.settings[voice_i].note_start_height,
            self.settings[voice_i].note_height,
            self.settings[voice_i].start_scale_function,
        )

    def scale_factors(self, t_until, voice_i):
        scale_x_factor = self._scale_x_factor(t_until, voice_i)
        if t_until >= 0:
            if self.equal_end_xy_size[voice_i]:
                return scale_x_factor, scale_x_factor
        elif self.equal_start_xy_size[voice_i]:
            return scale_x_factor, scale_x_factor
        return scale_x_factor, self._scale_y_factor(t_until, voice_i)

    def line_scale_factor(self, t_until, voice_i):
        if t_until >= 0:
            return self._get_scale_factor(
                t_until,
                self.settings[voice_i].frame_line_end,
                self.settings[voice_i].line_end_size,
                1,
                self.settings[voice_i].end_scale_function,
            )
        return self._get_scale_factor(
            -t_until,
            self.settings[voice_i].frame_line_start,
            self.settings[voice_i].line_start_size,
            1,
            self.settings[voice_i].start_scale_function,
        )

    def highlight_factor(self, t_until_attack, voice_i):
        if self.settings[voice_i].highlight_strength <= 0:
            return 0
        if 0 <= t_until_attack <= self.settings[voice_i].highlight_start:
            return -t_until_attack / self.settings[voice_i].highlight_start + 1
        if 0 < -t_until_attack <= self.settings[voice_i].highlight_end:
            return t_until_attack / self.settings[voice_i].highlight_end + 1
        return 0
