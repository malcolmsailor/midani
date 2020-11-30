import collections
import dataclasses
import math
import random
import typing

import midani_colors

# TODO revise this class?
class Note:
    def __init__(self, p, t1, t2):
        # pitch
        self.pitch = p
        # start time
        self.start = t1
        # end time
        self.end = t2
        # for convenience
        self.dur = t2 - t1
        self.mid = t1 + (t2 - t1) / 2


@dataclasses.dataclass
class RectTuple:
    note: Note
    scale_x_factor: float
    scale_y_factor: float
    flutter: float
    color: typing.Tuple[int, int, int]
    highlight_factor: float

    @property
    def pitch(self):
        return self.note.pitch + self.flutter


@dataclasses.dataclass
class LineTuple:
    note: Note
    scale_factor: float
    flutter: float
    color: typing.Tuple[int, int, int]
    highlight_factor: float

    @property
    def pitch(self):
        return self.note.pitch + self.flutter


class PitchFlutter:
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
        self.flutter_sin_factor = self.flutter_period * math.pi

    def __call__(self, now):
        return math.sin(now * self.flutter_sin_factor) * self.flutter_size


class Window:
    def __init__(self, settings):
        self.frame_len = settings.frame_len
        self.frame_position = settings.frame_position
        self.start_time = settings.start_time
        self.end_time = settings.end_time
        self.final_time = settings.final_time
        self.intro = settings.intro
        self.outro = settings.outro
        self.start_time = settings.start_time
        self.bg_colors = settings.bg_colors
        self.start_bg_color = settings.start_bg_color
        self.end_bg_color = settings.end_bg_color
        self.bg_color_gradients = settings.bg_color_gradients
        self.bg_times = settings.bg_clock_times
        self.bg_time_i = 0

    def _update_bg_times(self):
        try:
            if self._now < self.last_now:
                raise ValueError
        except AttributeError:
            pass
        self.last_now = self._now
        try:
            while self._now > self.bg_times[self.bg_time_i + 1]:
                self.bg_time_i += 1
        except IndexError:
            self.next_bg_time = self.end_time
        else:
            self.next_bg_time = self.bg_times[self.bg_time_i + 1]
        self.prev_bg_time = self.bg_times[self.bg_time_i]

    def bg_color(self):
        """Meant to be called with now in montonically ascending sequence,
        raises a value error otherwise."""
        # "between start and end"
        if self.start_time <= self._now <= self.final_time:
            self._update_bg_times()
            prev_bg_color = self.bg_colors[self.bg_time_i % len(self.bg_colors)]
            if not self.bg_color_gradients:
                return prev_bg_color
            bg_prop = (self._now - self.prev_bg_time) / (
                self.next_bg_time - self.prev_bg_time
            )
            next_bg_color = self.bg_colors[
                (self.bg_time_i + 1) % len(self.bg_colors)
            ]
        # "before start"
        elif self._now < self.start_time:
            prev_bg_color = self.start_bg_color
            if not self.bg_color_gradients:
                return prev_bg_color
            next_bg_color = self.bg_colors[0]
            # In first version of the script, this has a considerably more
            # complicated expression that I'm uncertain of the motivation for
            bg_prop = 1 - (self.start_time - self._now) / self.intro
        # "after end"
        elif self._now > self.end_time:
            next_bg_color = self.end_bg_color
            if not self.bg_color_gradients:
                return next_bg_color
            prev_bg_color = self.bg_colors[self.bg_time_i % len(self.bg_colors)]
            bg_prop = (self._now - self.end_time) / self.outro
        return midani_colors.blend_colors(
            prev_bg_color, next_bg_color, bg_prop,
        )

    def get_first_now(self):
        if self.intro >= 0:
            return -self.intro + self.start_time
        return (
            -math.floor(self.frame_len * self.frame_position) + self.start_time
        )

    def in_range(self, time):
        # return time <= self.end_time + math.ceil(
        #     self.frame_len * (1 - self.frame_position)
        # )
        return time <= self.end_time + self.outro

    def update(self, now):
        self._now = now
        self._start = now - self.frame_len * self.frame_position
        self._end = now + self.frame_len * (1 - self.frame_position)

    @property
    def start(self):  # pylint: disable=missing-docstring
        return self._start

    @property
    def end(self):  # pylint: disable=missing-docstring
        return self._end

    @property
    def bottom(self):
        # TODO
        return 0

    @property
    def top(self):
        # TODO
        return 1

    @property
    def range(self):
        return 1

    @property
    # TODO add to class docstring
    def now(self):  # pylint: disable=missing-docstring
        return self._now


# class Scaler:
#     def __init__(self, end_or_start, start_or_end_size, voice_size, scale_func):
#         self.end_or_start = end_or_start
#         self.start_or_end_size = start_or_end_size
#         self.voice_size = voice_size
#         self.scale_func = scale_func
#
#     def get_scale_factor(self, t_until):
#         return (
#             (1 - self.scale_func(t_until / self.end_or_start))
#             * (1 - self.start_or_end_size)
#             + self.start_or_end_size
#         ) * self.voice_size


class PitchRange:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._l_pitch = None
        self._h_pitch = None

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def append(self, note):
        super().append(note)
        self.update_from_pitch(note.pitch)


class Channel(PitchRange):
    def __init__(self, channel_i, settings):
        super().__init__()
        self.l_pitch_padding = settings.channel_settings[channel_i][
            "l_pitch_padding"
        ]
        self.height = settings.channel_heights[channel_i]
        self.window_range = 1  # TODO
        self.offset = settings.channel_offsets[channel_i]
        self.h_factor = settings.out_height / self.height

    def proportion(self, pitch):
        # TODO shouldn't this be *plus* self.l_pitch_padding?
        return (
            (pitch - self.l_pitch + self.l_pitch_padding)
            / self.pitch_range
            * self.height
        )

    @property
    # TODO add to class docstring
    def note_height(self):  # pylint: disable=missing-docstring
        return 1 / self.pitch_range * self.height

    def y_position(self, pitch):
        return self.proportion(pitch) * self.window_range + self.offset


class PitchTable(PitchRange, list):
    def __init__(self, score, settings, tempo_changes, *args, **kwargs):
        super().__init__()
        self.settings = settings
        self.equal_start_xy_size = (
            settings.note_start_x_size == settings.note_start_y_size
        )
        self.equal_end_xy_size = (
            settings.note_end_x_size == settings.note_end_y_size
        )
        self.voice_ranges = []
        self.l_pitch = None
        self.h_pitch = None
        self.channels = {
            chan_i: Channel(chan_i, settings)
            for chan_i in range(settings.num_channels)
        }
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
                #     self.voice_ranges.append((0, 0))
                continue
            for note in voice:
                attack_ctime = tempo_changes.ctime_from_btime(note.attack_time)
                end_dur_ctime = tempo_changes.ctime_from_btime(
                    note.attack_time + note.dur
                )
                pitch = note.pitch + pitch_displacement
                voice_list.append(Note(pitch, attack_ctime, end_dur_ctime))
            if voice_list:
                self.channels[chan_assmt].update_from_pitch(voice_list.l_pitch)
                self.channels[chan_assmt].update_from_pitch(voice_list.h_pitch)
        for channel in self.channels.values():
            if channel.l_pitch is not None:
                self.update_from_pitch(channel.l_pitch)
                self.update_from_pitch(channel.h_pitch)

        for voice_i, voice in enumerate(self):
            if "take_l_pitch_from_voice" in settings.voice_settings[voice_i]:
                voice.l_pitch = self[
                    voice_settings[voice_i]["take_l_pitch_from_voice"]
                ].l_pitch
            if "take_h_pitch_from_voice" in settings.voice_settings[voice_i]:
                voice.h_pitch = self[
                    voice_settings[voice_i]["take_h_pitch_from_voice"]
                ].h_pitch
        # Get pitch_flutters
        self.pitch_flutters = {}
        # for channel_i in range(settings.num_channels):
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

            # self.pitch_flutters[channel_i] = channel_flutters

    @staticmethod
    def _get_scale_factor(
        t, end_or_start, start_or_end_size, voice_size, scale_func
    ):
        try:
            return (
                (1 - scale_func(t / end_or_start)) * (1 - start_or_end_size)
                + start_or_end_size
            ) * voice_size
        except:
            breakpoint()

    def _scale_x_factor(self, t_until, voice_i):
        if t_until >= 0:
            return self._get_scale_factor(
                t_until,
                self.settings.note_end,
                self.settings.note_end_x_size,
                self.settings[voice_i]["size_x"],
                self.settings.start_scale_function,
            )
        return self._get_scale_factor(
            -t_until,
            self.settings.note_start,
            self.settings.note_start_x_size,
            self.settings[voice_i]["size_x"],
            self.settings.end_scale_function,
        )

    def _scale_y_factor(self, t_until, voice_i):
        if t_until >= 0:
            return self._get_scale_factor(
                t_until,
                self.settings.note_end,
                self.settings.note_end_y_size,
                self.settings[voice_i]["size_y"],
                self.settings.start_scale_function,
            )
        return self._get_scale_factor(
            -t_until,
            self.settings.note_start,
            self.settings.note_start_y_size,
            self.settings[voice_i]["size_y"],
            self.settings.end_scale_function,
        )

    def scale_factors(self, t_until, voice_i):
        scale_x_factor = self._scale_x_factor(t_until, voice_i)
        if t_until >= 0:
            if self.equal_start_xy_size:
                return scale_x_factor, scale_x_factor
        elif self.equal_end_xy_size:
            return scale_x_factor, scale_x_factor
        return scale_x_factor, self._scale_y_factor(t_until, voice_i)

    def line_scale_factor(self, t_until, voice_i):
        if t_until >= 0:
            return self._get_scale_factor(
                t_until,
                self.settings.line_end,
                self.settings.line_end_size,
                # self.settings[voice_i]["size"],
                1,  # TODO should this be a setting?
                self.settings.start_scale_function,
            )
        return self._get_scale_factor(
            -t_until,
            self.settings.line_start,
            self.settings.line_start_size,
            # self.settings[voice_i]["size"],
            1,
            self.settings.end_scale_function,
        )

    def highlight_factor(self, t_until_attack):
        if self.settings.highlight_strength <= 0:
            return 0
        if 0 <= t_until_attack <= self.settings.highlight_start:
            return -t_until_attack / self.settings.highlight_start + 1
        elif 0 < -t_until_attack <= self.settings.highlight_end:
            return t_until_attack / self.settings.highlight_end + 1
        return 0

    def highlight_strength(self):
        return 0  # TODO
