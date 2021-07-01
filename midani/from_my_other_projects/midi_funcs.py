import collections
import fractions
import warnings

import mido

import midani.from_my_other_projects.note_classes as note_classes
import midani.from_my_other_projects.tuning as tuning

NUM_CHANNELS = 16

# pitch_bend_tuple macros
MIDI_NUM = 0
PITCH_BEND = 1


# def pitch_list_to_midi(pitch_list, fname, tet=12, dur=4, tempo=120):
#     """# TODO doc
#     If a list of lists, writes as homophonic chords. Otherwise writes a melody.
#     """
#     if isinstance(pitch_list, np.ndarray):
#         if pitch_list.ndim != 2:
#             raise ValueError("If passing a np array, must be 2-dimensional")
#     elif not mal_iter.is_list_of_lists(pitch_list):
#         if mal_iter.is_list_of_lists(pitch_list, all_items=False):
#             raise ValueError(
#                 "Either every item in input list must be a list "
#                 "or none of them must be."
#             )
#         pitch_list = [[item,] for item in pitch_list]
#
#     mf = MIDIFile(1, adjust_origin=True)
#     mf.addTempo(0, 0, tempo)
#
#     if tet != 12:
#         pitch_dict = tuning.return_pitch_bend_tuple_dict(tet)
#
#     track = 0
#     velocity = 96
#     time = 0
#
#     for pitches in pitch_list:
#         for channel_i, pitch in enumerate(pitches):
#             if tet == 12:
#                 mf.addNote(track, channel_i, pitch, time, dur, velocity)
#             else:
#                 add_note_and_pitch_bend(
#                     mf,
#                     pitch_dict[pitch],
#                     time,
#                     dur,
#                     track=track,
#                     channel=channel_i,
#                     velocity=velocity,
#                 )
#         time += dur
#     with open(fname, "wb") as outf:
#         mf.writeFile(outf)


def _pitch_bend_handler(pitch_bend_dict, track_i, msg):
    """Used by read_midi_to_internal_data()."""
    pitch_bend_dict[track_i][msg.channel] = msg.pitch


def _note_on_handler(
    note_on_dict, pb_dict, inverse_pb_tup_dict, track_i, msg, tet=12
):
    """Used by read_midi_to_internal_data()."""

    channel = msg.channel
    midinum = msg.note

    if tet != 12:
        pitch_bend = pb_dict[track_i][channel]
        pitch = inverse_pb_tup_dict[(midinum, pitch_bend)]

    else:
        pitch = midinum

    note_on_dict[track_i][channel][midinum] = (msg, pitch)


def _note_off_handler(
    note_on_dict, track_i, msg, ticks_per_beat, max_denominator=8192
):
    """Used by read_midi_to_internal_data()."""

    channel = msg.channel
    midinum = msg.note
    tick_release = msg.time
    note_on_msg, pitch = note_on_dict[track_i][channel][midinum]
    velocity = note_on_msg.velocity
    tick_attack = note_on_msg.time

    tick_dur = tick_release - tick_attack
    attack = fractions.Fraction(tick_attack, ticks_per_beat).limit_denominator(
        max_denominator=max_denominator
    )
    dur = fractions.Fraction(tick_dur, ticks_per_beat).limit_denominator(
        max_denominator=max_denominator
    )

    note_object = note_classes.Note(
        pitch, attack, dur, velocity=velocity, choir=channel
    )

    return note_object


def _return_sorted_midi_tracks(in_mid):
    """Used by read_midi_to_internal_data()."""

    def _sorter_string(msg):
        if msg.type == "pitchwheel":
            return "aaaa"
        return msg.type

    out = []
    for track in in_mid.tracks:
        out.append([])
        tick_time = 0
        for msg in track:
            tick_time += msg.time
            if isinstance(msg, mido.midifiles.meta.MetaMessage):
                out[-1].append(AbsoluteMetaMidiMsg(msg, tick_time))
            else:
                out[-1].append(AbsoluteMidiMsg(msg, tick_time))

        out[-1].sort(key=lambda msg: _sorter_string(msg))
        out[-1].sort(key=lambda msg: msg.time)

    return out


def read_midi_to_internal_data(
    in_midi_fname,
    tet=12,
    time_sig=None,
    track_num_offset=0,
    max_denominator=8192,
    first_note_at_0=False,
    min_attack_to_adjust=4,
    split_tracks_to_voices=True,
    split_channels_to_voices=False,
):
    """Reads midi file into a Score() instance.

    NB Because one can't tell from a note off event when a note might have
    started, or vice versa, I decided not to include "start" and "end"
    parameters. To truncate the read file, one can call the get_passage()
    method of the returned Score() instance.

    Args:
        in_midi_fname: path name to a midi file.

    Keyword args:
        tet: int. Default 12.
        time_sig: # TODO doc
        track_num_offset: # TODO doc
        max_demoninator: int.
        first_note_at_0: boolean. Whether to displace the first note of
            the midi file to time 0 (if it doesn't already occur at this
            time). Default: False. If True, only applies if first note's
            attack is >= min_attack_to_adjust.
        min_attack_to_adjust: number. If first_note_at_0 is True, then only
            displace first note if its attack is >= this number.
        split_tracks_to_voices: boolean. If True, notes from different midi
            tracks are mapped to different "voices" in the output Score
            Default: True
        split_channels_to_voices: boolean. If True, notes from different midi
            channels are mapped to different "voices" in the output Score.
            Default: False

    Returns:
        Score() instance
    """

    in_mid = mido.MidiFile(in_midi_fname)
    num_tracks = len(in_mid.tracks)
    if num_tracks == 1:
        warnings.warn(
            "Midi files of just one track exported from Logic "
            "don't put meta messages on a separate track. Support "
            "for these is not yet implemented and there is likely to "
            "be a crash very soon..."
        )

    ticks_per_beat = in_mid.ticks_per_beat

    if max_denominator == 0:
        max_denominator = 8192

    num_voices = num_tracks - 1 if split_tracks_to_voices else 1
    if split_channels_to_voices:
        num_voices *= NUM_CHANNELS

    internal_data = note_classes.Score(
        tet=tet, num_voices=num_voices, time_sig=time_sig
    )
    if track_num_offset:
        for voice in internal_data.voices:
            voice.voice_i += track_num_offset

    # Sorting the tracks avoids orphan note or pitchwheel events.
    sorted_tracks = _return_sorted_midi_tracks(in_mid)

    pitch_bend_tuple_dict = tuning.return_pitch_bend_tuple_dict(tet)

    inverse_pb_tup_dict = {}
    for pitch, pb_tup in pitch_bend_tuple_dict.items():
        inverse_pb_tup_dict[pb_tup] = pitch

    pitch_bend_dict = {
        i: {j: {} for j in range(NUM_CHANNELS)} for i in range(num_tracks)
    }
    note_on_dict = {
        i: {j: {} for j in range(NUM_CHANNELS)} for i in range(num_tracks)
    }

    for track_i, track in enumerate(sorted_tracks):
        for msg in track:
            if msg.type == "pitchwheel":
                _pitch_bend_handler(pitch_bend_dict, track_i, msg)
            elif msg.type == "note_on" and msg.velocity > 0:
                _note_on_handler(
                    note_on_dict,
                    pitch_bend_dict,
                    inverse_pb_tup_dict,
                    track_i,
                    msg,
                    tet=tet,
                )
            elif msg.type == "note_on" and msg.velocity == 0 and msg.note == 0:
                # JRP scores seem to have note_on events with velocity and
                # note 0 at the end of scores. We can ignore these.
                continue
            elif msg.type == "note_off" or (
                msg.type == "note_on" and msg.velocity == 0
            ):
                note_object = _note_off_handler(
                    note_on_dict,
                    track_i,
                    msg,
                    ticks_per_beat,
                    max_denominator=max_denominator,
                )
                voice_i = track_i - 1 if split_tracks_to_voices else 0
                if split_channels_to_voices:
                    voice_i = voice_i * NUM_CHANNELS + msg.channel
                internal_data.add_note_object(
                    voice_i, note_object, update_sort=False
                )
            else:
                msg.time = fractions.Fraction(msg.time, ticks_per_beat)
                if track_i == 0:
                    internal_data.add_meta_message(msg)
                else:
                    internal_data.add_other_message(track_i - 1, msg)
        # Replaced this code with voice.update_sort() below
        # if track_i != 0:
        # internal_data.voices[track_i - 1].update_sort()

    for voice in internal_data.voices:
        voice.update_sort()
    internal_data.remove_empty_voices()
    if first_note_at_0 is False:
        return internal_data

    first_attack = internal_data.get_total_len()
    for voice in internal_data.voices:
        first_attack_in_voice = min(voice.data.keys())
        if first_attack_in_voice < first_attack:
            first_attack = first_attack_in_voice

    # If the first attack is smaller than min_attack_to_adjust, don't
    # displace the score.

    # if first_note_at_0 is None and
    if first_attack < min_attack_to_adjust:
        return internal_data

    if first_attack > 0:
        internal_data.attacks_adjusted_by = -first_attack
        internal_data.displace_passage(-first_attack)

    return internal_data


class AbsoluteMidiMsg(mido.Message):
    """A child class of the Message class from the mido library. The only
    change is that the time is specified in absolute ticks.

    Call with AbsoluteMidiMsg(msg, tick_time) where "msg" is a mido Message
    and tick_time is the time in ticks.

    Use with caution since the mido methods may rely on relative tick_times.
    """

    def __init__(self, msg, tick_time):
        super().__init__(msg.type)
        self_vars = vars(self)
        msg_vars = vars(msg)
        for msg_attribute, value in msg_vars.items():
            self_vars[msg_attribute] = value
        self.time = tick_time


class AbsoluteMetaMidiMsg(mido.MetaMessage):
    """A child class of the MetaMessage class from the mido library. The only
    change is that the time is specified in absolute ticks.

    Call with AbsoluteMetaMidiMsg(msg, tick_time) where "msg" is a mido
    MetaMessage and tick_time is the time in ticks.

    Use with caution since the mido methods may rely on relative tick_times.
    """

    def __init__(self, msg, tick_time):
        super().__init__(msg.type)
        self_vars = vars(self)
        msg_vars = vars(msg)
        for msg_attribute, value in msg_vars.items():
            self_vars[msg_attribute] = value
        self.time = tick_time


# class MidiSettings:
#     def __init__(self):
#         self.num_channels_pitch_bend_loop = 9
#         self.pitch_bend_time_prop = 2 / 3
#         self.note_counter = collections.Counter()
#         self.tet = 12
#
#
# def add_track(track_i, track, midi_settings, mf):
#     for msg in track.other_messages:
#         if msg.type in ("track_name", "end_of_track", "instrument_name"):
#             continue
#         elif msg.type == "program_change":
#             mf.addProgramChange(track_i, msg.channel, msg.time, msg.program)
#         else:
#             print(f"Message of type {msg.type} not written to file.")
#
#     no_finetuning = all([note.finetune == 0 for note in track])
#     # if not no_finetuning:
#     #     try:
#     #         midi_settings.pitch_bend_tuple_dict
#     #     except AttributeError:
#     #         midi_settings.pitch_bend_tuple_dict = (
#     #             er_tuning.return_pitch_bend_tuple_dict(midi_settings.tet))
#
#     for note in track:
#         if midi_settings.tet == 12 and no_finetuning:
#             mf.addNote(
#                 track_i,
#                 note.choir,
#                 note.pitch,
#                 note.attack_time,
#                 note.dur,
#                 note.velocity,
#             )
#         else:
#             channel = (
#                 midi_settings.note_counter[track_i]
#                 % midi_settings.num_channels_pitch_bend_loop
#             )
#             note_count = midi_settings.note_counter[track_i]
#             midi_settings.note_counter[track_i] += 1
#             midi_num, pitch_bend = midi_settings.pitch_bend_tuple_dict[
#                 note.pitch
#             ]
#             if note.finetune:
#                 midi_num, pitch_bend = er_tuning.finetune_pitch_bend_tuple(
#                     (midi_num, pitch_bend), note.finetune
#                 )
#             prev_time_on_channel = midi_settings.pitch_bend_time_dict[track_i][
#                 note_count % midi_settings.num_channels_pitch_bend_loop
#             ]
#             midi_settings.pitch_bend_time_dict[track_i][
#                 note_count % midi_settings.num_channels_pitch_bend_loop
#             ] = note.attack_time
#             if prev_time_on_channel == 0:
#                 pitch_bend_time = 0
#             else:
#                 pitch_bend_time = (
#                     prev_time_on_channel
#                     + midi_settings.pitch_bend_time_prop
#                     * (note.attack_time - prev_time_on_channel)
#                 )
#             add_note_and_pitch_bend_separately(
#                 mf,
#                 (midi_num, pitch_bend),
#                 note.attack_time,
#                 note.dur,
#                 pitch_bend_time,
#                 track_i,
#                 channel,
#                 note.velocity,
#             )


# def write_midi(score_obj, midi_fname, abbr_track_names=True):
#     """Write a midi file, without an associated ERSettings class (e.g.,
#     if processing an external midi file).
#     """
#
#     midi_settings = MidiSettings()
#     midi_settings.num_tracks = score_obj.num_voices
#     tet = score_obj.tet
#
#     # If the file is in 12 tet and features no finetuning then these steps are
#     # not necessary but for the moment it seems like more effort than it's
#     # worth to check:
#     midi_settings.tet = tet
#     midi_settings.pitch_bend_time_dict = {
#         track_i: [0 for i in range(midi_settings.num_channels_pitch_bend_loop)]
#         for track_i in range(midi_settings.num_tracks)
#     }
#     midi_settings.pitch_bend_tuple_dict = tuning.return_pitch_bend_tuple_dict(
#         tet
#     )
#
#     mf = MIDIFile(midi_settings.num_tracks, adjust_origin=True)
#
#     # write_track_names(
#     #     midi_settings, mf, midi_fname, abbr_track_names=abbr_track_names)
#
#     # write_meta_messages(score_obj, mf)
#
#     for track_i, track in enumerate(score_obj.voices):
#         add_track(track_i, track, midi_settings, mf)
#
#     with open(midi_fname, "wb") as outf:
#         mf.writeFile(outf)
#
#
# def add_note_and_pitch_bend(
#     mf, pitch_bend_tuple, time, dur, track=0, channel=0, velocity=64
# ):
#     """Adds simultaneous note and pitchwheel event."""
#     mf.addPitchWheelEvent(track, channel, time, pitch_bend_tuple[PITCH_BEND])
#     mf.addNote(track, channel, pitch_bend_tuple[MIDI_NUM], time, dur, velocity)
#
#
# if __name__ == "__main__":
#     pitch_list = (
#         np.array(
#             [
#                 [-39, 0, 10, 20],
#                 [-29, 0, 10, 21],
#                 [-19, 0, 11, 21],
#                 [-40, 1, 11, 21],
#             ]
#         )
#         + 5 * 31
#     )
#     pitch_list_to_midi(pitch_list, "test.mid", tet=31)
