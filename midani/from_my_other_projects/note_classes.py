"""Provides a Score class that stores Voice classes which store Note classes,
together with associated methods.
"""
import collections
import copy
import fractions
import numbers
import warnings

import mido

import midani.from_my_other_projects.mal_misc as mal_misc

# TODO update from er_classes

# import spell

# constants for writing notes
DEFAULT_VELOCITY = 96
DEFAULT_CHOIR = 0


class Note:
    """Stores a note.

    Attributes:
        pitch: an integer.
        attack_time: a fraction.
        dur: a fraction.
        velocity: an integer 0-127.
        choir: an integer.
        voice: an integer, or None. A place to store the voice that
            a note belongs to.
    """

    def __init__(
        self,
        pitch,
        attack_time,
        dur,
        velocity=DEFAULT_VELOCITY,
        choir=DEFAULT_CHOIR,
        voice=None,
        finetune=0,
    ):
        self.pitch = pitch
        self.attack_time = attack_time
        self.dur = dur
        self.velocity = velocity
        self.choir = choir
        self.voice = voice
        # self.finetune (in cents) can be used for arbitrary tuning
        self.finetune = finetune

    def __repr__(self):
        out = (
            "<Note pitch={} attack={:f} dur={:f} vel={} choir={} "
            "voice={}>\n".format(
                self.pitch,
                float(self.attack_time),
                float(self.dur),
                self.velocity,
                self.choir,
                self.voice,
            )
        )
        return out


class Voice(collections.UserDict):
    """A dictionary of lists of Note objects, together with methods for
    working with them.

    Can be iterated over (e.g., for note in voice [where "voice" is a
    Voice object]) and reversed (e.g., reversed(voice)). This will
    give the note objects sorted by attack time and secondarily by
    durations.

    Attributes:
        data: a dictionary. Keys are attack_times (fractions), values are
            lists of Note objects, sorted by duration.
        other_messages: a list in which other midi messages are stored
            when constructing the voice from a midi file.
        max_attack_time: fraction. Used to monitor whether to re-sort
            the dictionary (i.e., if a new attack time smaller than
            max_attack_time is added).
        voice_i: int. The index number of the voice, if stored in a
            Score object.
        tet: int.
        range: Nonetype, or tuple of two ints. Used in certain
            transformers.
    """

    def __init__(self, voice_i=None, tet=12, voice_range=None):
        super().__init__()
        self.other_messages = []
        # self.max_attack_time is used to check whether to sort the
        #   dictionary after adding a new note
        self.max_attack_time = 0
        self.voice_i = voice_i
        self.tet = tet
        # self.speller = spell.Speller(tet)
        self.range = voice_range
        self.sort_up_to_date = 0
        self.reversed_up_to_date = -1

    def __iter__(self):
        for attack_time in self.data:
            notes = sorted(self.data[attack_time], key=lambda x: x.pitch)
            notes = sorted(notes, key=lambda x: x.dur)
            for note_object in notes:
                yield note_object

    def __reversed__(self):
        if self.reversed_up_to_date != self.sort_up_to_date:
            self.reversed_voice = dict(
                sorted(self.data.items(), key=lambda x: x[0], reverse=True)
            )
            for attack_time in self.reversed_voice:
                self.reversed_voice[attack_time].sort(
                    key=lambda x: x.dur, reverse=True
                )
            self.reversed_up_to_date = self.sort_up_to_date
        for attack_time in self.reversed_voice:
            # notes = sorted(
            #     self.data[attack_time], key=lambda x: x.dur, reverse=True)
            for note_object in self.reversed_voice[attack_time]:
                yield note_object

    def __str__(self):
        strings = []
        strings.append("#" * 51)
        for note in self:
            strings.append(
                "Attack:{:>10.3}  Pitch:{:>5}  Duration:{:>10.3}"
                "".format(
                    float(note.attack_time),
                    # self.speller.spell(note.pitch),
                    note.pitch,
                    float(note.dur),
                )
            )
        strings.append("\n")
        return "\n".join(strings)[:-2]

    def is_polyphonic(self):
        for attack_time in self.data:
            if len(self.data[attack_time]) > 1:
                return True
        return False

    def slice_keys(self, slice_):
        if isinstance(slice_, int):
            start = slice_
            stop = None
            step = None
        else:
            start = slice_.start
            stop = slice_.stop
            step = slice_.step
        return list(self.data.keys())[start:stop:step]

    def update_sort(self):
        self.data = dict(sorted(self.data.items(), key=lambda x: x[0]))
        for attack_time in self.data:
            self.data[attack_time].sort(key=lambda x: x.dur)

    def update_attack_time(self, attack_time):
        if attack_time <= self.max_attack_time:
            # This condition means that update secondary sort will not
            # necessarily take place, but since nothing depends on the
            # secondary sort the speed gain is probably worth it.
            #
            # changed my mind and commented the condition out:
            # if attack_time not in self.data:
            self.update_sort()
        else:
            self.max_attack_time = attack_time

    def add_note(
        self,
        pitch,
        attack_time,
        dur,
        velocity=DEFAULT_VELOCITY,
        choir=DEFAULT_CHOIR,
        update_sort=True,
    ):
        """Adds a note."""
        try:
            self[attack_time].append(
                Note(
                    pitch,
                    attack_time,
                    dur,
                    velocity=velocity,
                    choir=choir,
                    voice=self.voice_i,
                )
            )
        except KeyError:
            self[attack_time] = [
                Note(
                    pitch,
                    attack_time,
                    dur,
                    velocity=velocity,
                    choir=choir,
                    voice=self.voice_i,
                ),
            ]
        if update_sort:
            self.update_attack_time(attack_time)
        self.sort_up_to_date += update_sort

    def add_note_object(self, note_object, update_sort=True):
        """Adds a note object."""
        note_object.voice = self.voice_i
        # if note_object.attack_time not in self:
        #     self[note_object.attack_time] = []
        try:
            self[note_object.attack_time].append(note_object)
        except KeyError:
            self[note_object.attack_time] = [
                note_object,
            ]
        if update_sort:
            self.update_attack_time(note_object.attack_time)
        self.sort_up_to_date += update_sort

    def move_note(self, note_object, new_attack_time, update_sort=True):
        """Moves a note object to a new attack time."""
        self.remove_note_object(note_object)
        note_object.attack_time = new_attack_time
        self.add_note_object(note_object, update_sort=update_sort)

    def remove_note(self, pitch, attack_time, dur=None):
        """Removes a note from the voice.

        Like list.remove, removes the first note that it finds
        that matches the specified criteria -- so if there is
        more than one identical note, the others will remain.
        If dur is not specified, then matches any dur.
        """

        class RemoveNoteError(Exception):
            pass

        try:
            notes = self.data[attack_time]
        except KeyError:
            raise RemoveNoteError(f"No notes at attack time {attack_time}")
        remove_i = -1
        for note_i, note in enumerate(notes):
            if note.pitch == pitch:
                if dur and note.dur != dur:
                    continue
                remove_i = note_i
                break
        if remove_i < 0:
            if dur:
                raise RemoveNoteError(
                    f"No note of pitch {pitch} and dur {dur} at attack "
                    f"time {attack_time}"
                )
            raise RemoveNoteError(
                f"No note of pitch {pitch} at attack " f"time {attack_time}"
            )
        notes.pop(remove_i)
        if not notes:
            del self.data[attack_time]

    def remove_note_object(self, note_object):
        class RemoveNoteObjectError(Exception):
            pass

        attack_time = note_object.attack_time
        try:
            notes = self.data[attack_time]
        except KeyError:
            raise RemoveNoteObjectError(
                f"No attacks at {attack_time} in voice {self.voice_i}."
            )
        notes.remove(note_object)
        if not notes:
            del self.data[attack_time]

    def add_rest(self, attack_time, dur, update_sort=True):
        """Adds a 'rest'."""
        try:
            self[attack_time].append(
                Note(
                    None,
                    attack_time,
                    dur,
                    velocity=None,
                    choir=None,
                    voice=self.voice_i,
                )
            )
        except KeyError:
            self[attack_time] = [
                Note(
                    None,
                    attack_time,
                    dur,
                    velocity=None,
                    choir=None,
                    voice=self.voice_i,
                ),
            ]
        if update_sort:
            self.update_attack_time(attack_time)
        self.sort_up_to_date += update_sort

    def add_other_message(self, message):
        self.other_messages.append(message)

    def append(self, other_voice, offset=0):
        """Appends the notes of another Voice object."""
        for note_object in other_voice:
            note_copy = copy.copy(note_object)
            note_copy.attack_time += offset
            self.add_note_object(note_copy, update_sort=False)
        self.update_sort()
        self.sort_up_to_date += 1

    def get_sounding_pitches(
        self, attack_time, dur=0, min_attack_time=0, min_dur=0
    ):

        sounding_pitches = set()
        end_time = attack_time + dur
        times = list(self.data.keys())
        i = mal_misc.binary_search(times, end_time)
        while i is not None:
            try:
                time = times[i]
            except IndexError:
                i -= 1
                continue
            i -= 1
            notes = self.data[time]
            break_out = False
            for note in reversed(notes):
                if dur > 0 and note.attack_time >= end_time:
                    continue
                elif note.attack_time > end_time:
                    continue
                if note.attack_time < min_attack_time:
                    break_out = True
                    break
                if note.attack_time + note.dur <= attack_time:
                    continue
                if note.dur >= min_dur:
                    sounding_pitches.add(note.pitch)
            if i < 0 or break_out:
                break

        return list(sorted(sounding_pitches))

    def get_all_pitches_attacked_during_duration(self, attack_time, dur):
        return self.get_sounding_pitches(
            attack_time, dur=dur, min_attack_time=attack_time
        )

    def get_prev_n_pitches(
        self,
        n,
        time,
        min_attack_time=0,
        stop_at_rest=False,
        include_start_time=False,
    ):
        """Returns previous n pitches (attacked before time).

        If pitches are attacked earlier than min_attack_time, -1 will be
        returned instead. Or, if stop_at_rest is True, then instead of any
        pitches earlier than the first rest, -1 will be returned in place.
        """

        attack_times = list(self.data.keys())
        i = mal_misc.binary_search(attack_times, time, not_found="force_upper")
        pitches = []
        if n <= 0:
            return pitches
        while i is not None:
            i -= 1
            if i < 0:
                break
            attack_time = last_attack_time = attack_times[i]
            if attack_time == time and not include_start_time:
                continue

            notes = self.data[attack_time]
            break_out = False
            for note in reversed(notes):
                if note.attack_time < min_attack_time:
                    break_out = True
                    break
                if (
                    stop_at_rest
                    and note.attack_time + note.dur < last_attack_time
                ):
                    break_out = True
                    break
                pitches.insert(0, note.pitch)
                last_attack_time = note.attack_time
                if len(pitches) == n:
                    break_out = True
                    break
            if break_out:
                break

        for i in range(n - len(pitches)):
            pitches.insert(0, -1)
        return pitches

    def get_prev_pitch(self, time, min_attack_time=0, stop_at_rest=False):
        """Returns previous pitch from voice."""
        return self.get_prev_n_pitches(
            1, time, min_attack_time=min_attack_time, stop_at_rest=stop_at_rest
        )[0]

    def get_last_n_pitches(
        self, n, time, min_attack_time=0, stop_at_rest=False
    ):
        """Returns last n pitches (including pitch attacked at time)."""
        return self.get_prev_n_pitches(
            n,
            time,
            min_attack_time=min_attack_time,
            stop_at_rest=stop_at_rest,
            include_start_time=True,
        )

    def get_prev_n_notes(
        self,
        n,
        time,
        min_attack_time=0,
        stop_at_rest=False,
        include_start_time=False,
    ):
        """Like get_prev_n_pitches, but returns Note objects.

        If notes are attacked earlier than min_attack_time, None will be
        returned instead. Or, if stop_at_rest is True, then instead of any
        pitches earlier than the first rest, None will be returned instead.
        """

        attack_times = list(self.data.keys())
        i = mal_misc.binary_search(attack_times, time)
        out_notes = []
        if n <= 0:
            return out_notes
        while i is not None:
            i -= 1
            if i < 0:
                break
            attack_time = attack_times[i]
            if attack_time == time and not include_start_time:
                continue

            notes = self.data[attack_time]
            break_out = False
            for note in reversed(notes):
                if note.attack_time < min_attack_time:
                    break_out = True
                    break
                if (
                    stop_at_rest
                    and note.attack_time + note.dur < last_attack_time
                ):
                    break_out = True
                    break
                out_notes.insert(0, note)
                last_attack_time = note.attack_time
                if len(out_notes) == n:
                    break_out = True
                    break
            if break_out:
                break

        for j in range(n - len(out_notes)):
            out_notes.insert(0, None)
        return out_notes

    def get_prev_note(self, time, min_attack_time=0, stop_at_rest=False):
        """Returns previous Note from voice."""
        return self.get_prev_n_notes(
            1, time, min_attack_time=min_attack_time, stop_at_rest=stop_at_rest
        )[0]

    def get_last_n_notes(self, n, time, min_attack_time=0, stop_at_rest=False):
        """Returns last n pitches (including pitch attacked at time)."""
        return self.get_prev_n_notes(
            n,
            time,
            min_attack_time=min_attack_time,
            stop_at_rest=stop_at_rest,
            include_start_time=True,
        )

    def get_passage(
        self,
        passage_start_time=None,
        passage_end_time=None,
        dont_overlap_start=True,
        end_time_refers_to_attack=True,
    ):

        """Returns a single voice of a given passage.

        Passage is inclusive of passage_start_time and exclusive of
        passage_end_time.

        Doesn't change the "voice" attributes of the notes.

        Keyword args:
            passage_start_time: time for passage to begin. If None, then
                takes all notes until passage_end_time. Default None.
            passage_end_time: time for passage to end. If None, then takes all
                notes after passage_start_time. Default None.
            dont_overlap_start: bool. If True, then passage only includes note
                attacked after passage_start_time. If False, also includes
                notes attacked before passage_start_time, but still sounding
                at passage_start_time. Default True.
            end_time_refers_to_attack: bool. If True, then notes that start
                before passage_end_time are included. If False, then notes that
                *end* before passage_end_time (inclusive) are included. Default True.
        """

        new_voice = Voice(tet=self.tet, voice_range=self.range)

        for note in self:
            attack_time = note.attack_time
            if passage_start_time is not None:
                if dont_overlap_start and attack_time < passage_start_time:
                    continue
                elif attack_time + note.dur < passage_start_time:
                    continue
            if passage_end_time is not None:
                if attack_time >= passage_end_time:
                    break
                elif (
                    not end_time_refers_to_attack
                    and attack_time + note.dur > passage_end_time
                ):
                    continue
            try:
                new_voice[attack_time].append(copy.copy(note))
            except KeyError:
                new_voice[attack_time] = [
                    copy.copy(note),
                ]

        return new_voice

    def repeat_passage(
        self, original_start_time, original_end_time, repeat_start_time
    ):
        """Repeats a voice."""
        repeated_notes = []
        for note in self:
            attack_time = note.attack_time
            if attack_time < original_start_time:
                continue
            if attack_time >= original_end_time:
                break
            repeat_time = repeat_start_time + attack_time - original_start_time
            repeat_note = copy.copy(note)
            repeat_note.attack_time = repeat_time
            repeated_notes.append(repeat_note)

        for repeat_note in repeated_notes:
            self.add_note_object(repeat_note, update_sort=False)
        self.update_sort()
        self.sort_up_to_date += 1

    def transpose(self, interval, start_time=0, end_time=None):
        """Transposes a passage."""

        for note in self:
            attack_time = note.attack_time
            if attack_time < start_time:
                continue
            if end_time is not None and attack_time >= end_time:
                break
            note.pitch += interval

    def displace_passage(self, displacement, start_time=None, end_time=None):
        if displacement == 0:
            return
        notes_to_move = []
        for note_object in self:
            if start_time and start_time > note_object.attack_time:
                continue
            if end_time and note_object.attack_time >= end_time:
                continue
            notes_to_move.append(note_object)

        for note_object in notes_to_move:
            self.remove_note_object(note_object)
            note_object.attack_time = note_object.attack_time + displacement
            if note_object.attack_time >= 0:
                self.add_note_object(note_object, update_sort=False)

        self.update_sort()
        self.sort_up_to_date += 1


class VoiceList(collections.UserList):
    def __init__(self, iterable=(), num_new_voices=None, existing_voices=()):
        super().__init__()
        self.data = list(iterable)
        if num_new_voices is None:
            self.num_new_voices = len(iterable)
        else:
            self.num_new_voices = num_new_voices
            if iterable and len(iterable) != num_new_voices:
                print(
                    "Warning: VoiceList constructor called with an iterable "
                    "and a num_new_voices, and length of iterable does not "
                    "agree."
                )
        self.existing_voices = existing_voices
        self.num_existing_voices = len(existing_voices)

    def __getitem__(self, key):
        if 0 <= key < self.num_new_voices:
            # try:
            return self.data[key]
            # except IndexError:
            #     breakpoint()
        if (
            self.num_new_voices
            < key
            <= self.num_new_voices + self.num_existing_voices
        ):
            # An IndexError will be raised between the indices
            #   for the new voices properly in this list and the
            #   existing voices. This must be so to permit
            #   iteration over the list proper. So, for instance,
            #   if there are 3 new voices and 2 existing voices,
            #   indices 0-2 will access the new voices and 4-5 the
            #   existing voices, while 3 will raise an IndexError.
            return self.existing_voices[key - self.num_new_voices - 1]
        if key < 0:
            return self.data[self.num_new_voices + key]
        raise IndexError()

    def append(self, item):
        self.data.append(item)
        self.num_new_voices += 1

    def extend(self, iterable):
        self.data.extend(iterable)
        self.num_new_voices += len(iterable)

    def insert(self, i, item):
        self.data.insert(i, item)
        self.num_new_voices += 1

    def remove(self, item):
        self.data.remove(item)
        self.num_new_voices -= 1

    def pop(self, i=None):
        if i is not None:
            out = self.data.pop(i)
        else:
            out = self.data.pop()
        self.num_new_voices -= 1
        return out

    def copy(self):
        return copy.deepcopy(self)


class HarmonyTimes:
    def __init__(self, start, end):
        self.start_time = start
        self.end_time = end


class Score:
    """Contains the notes, as well as many methods for working with them.

    Arguments:
        harmony_len: Used to construct attribute "harmony_times_dict"
            and associated methods. If passed, pass "total_len" as well.
        total_len: Total length of the music that will be stored. Only used
            in calculation of "harmony_times_dict", so you can add notes
            beyond this time without consequence.

    """

    def __str__(self, head=-1):
        strings = []
        for voice_type, voice_list in (
            ("EXISTING VOICE", self.existing_voices),
            ("VOICE", self.voices),
        ):
            for voice_i, voice in enumerate(voice_list):
                strings.append("#" * 51)
                strings.append(f"{voice_type} {voice_i}")
                strings.append("#" * 51)
                n = 0
                for note in voice:
                    if head > 0:
                        if n > head:
                            break
                        n += 1
                    strings.append(
                        "Attack:{:>10.3}  Pitch:{:>5}  Duration:{:>10.3}"
                        "".format(
                            float(note.attack_time),
                            # self.speller.spell(note.pitch),
                            note.pitch,
                            float(note.dur),
                        )
                    )
                strings.append("\n")
        return "\n".join(strings)[:-2]

    def head(self, head=15):
        return self.__str__(head=head)

    def __iter__(self):
        # This iterates over new *and* existing voices... is there any
        # use case for doing just one over the other?
        attack_times = []
        for voice_i in self.all_voice_is:
            attack_times += self.voices[voice_i].data.keys()
        attack_times = sorted(list(set(attack_times)))
        for attack_time in attack_times:
            out = []
            for voice_i in self.all_voice_is:
                try:
                    out += self.voices[voice_i].data[attack_time]
                except KeyError:
                    pass
            yield out

    def get_total_len(self):
        """Returns the length of the super pattern from 0 to the final note
        release.
        """
        total_len = 0
        for voice in self.voices:
            try:
                max_attack = max(voice.data)
            except ValueError:
                # if a voice is empty, max will return a ValueError
                continue
            max_dur = max([note.dur for note in voice[max_attack]])
            final_release = max_attack + max_dur
            if final_release > total_len:
                total_len = final_release

        return total_len

    def add_voice(self, voice=None, voice_i=None, voice_range=None):
        """Adds a voice."""
        if voice:
            self.voices.append(voice)
            if voice_i is not None:
                self.voices[-1].voice_i = voice_i
        else:
            if voice_i is None:
                voice_i = self.num_voices
            self.voices.append(
                Voice(voice_i=voice_i, tet=self.tet, voice_range=voice_range)
            )
        self.num_voices += 1
        return self.voices[self.num_voices - 1]

    def remove_empty_voices(self):
        """Removes any voices that contain no notes."""

        non_empty_voices = list(range(self.num_voices))
        for voice_i, voice in enumerate(self.voices):
            if not voice:
                non_empty_voices.remove(voice_i)
                self.num_voices -= 1

        new_voices = VoiceList()
        for non_empty_voice_i in non_empty_voices:
            new_voices.append(self.voices[non_empty_voice_i])
        self.voices = new_voices

    def add_note(
        self,
        voice_i,
        pitch,
        attack_time,
        dur,
        velocity=DEFAULT_VELOCITY,
        choir=DEFAULT_CHOIR,
    ):
        """Adds a note to the specified voice."""
        self.voices[voice_i].add_note(
            pitch, attack_time, dur, velocity=velocity, choir=choir
        )

    def add_note_object(self, voice_i, note_object, update_sort=True):
        """Adds a note object to the specified voice."""
        self.voices[voice_i].add_note_object(
            note_object, update_sort=update_sort
        )

    def add_other_message(self, voice_i, message):
        self.voices[voice_i].add_other_message(message)

    def add_meta_message(self, message):
        self.meta_messages.append(message)

    def attack(self, attack_time, voice_i):
        """Check if an attack occurs in the given voice
        at the specified time."""
        if attack_time in self.voices[voice_i]:
            return True
        return False

    def fill_with_rests(self, end_time):
        """Fills all silences with "rests" (Note classes with pitch,
        choir, and velocity all None).

        end_time must be passed (in order to fill the end of the last measure
        with rests).

        For now this is only used for writing kern files.
        """
        for voice_i, voice in enumerate(self.voices):
            temp_voice = Voice(
                voice_i=voice.voice_i, tet=voice.tet, voice_range=voice.range
            )
            time = 0
            prev_release = 0
            for note in voice:
                attack_time = note.attack_time
                if attack_time > prev_release:
                    rest_attack = prev_release
                    rest_dur = attack_time - prev_release
                    temp_voice.add_rest(rest_attack, rest_dur)
                prev_release = attack_time + note.dur
                temp_voice.add_note_object(note)
            if prev_release < end_time:
                rest_attack = prev_release
                rest_dur = end_time - prev_release
                temp_voice.add_rest(rest_attack, rest_dur)

            self.voices[voice_i] = temp_voice

    def displace_passage(
        self,
        displacement,
        start_time=None,
        end_time=None,
        apply_to_existing_voices=False,
    ):
        """Moves a passage forward or backward in time.

        Any notes whose attack times are moved before 0 will be deleted.

        Any meta messages whose attack times that would be displaced below
        time 0 are placed at time 0.

        If start_time is not specified, passage moved starts from beginning
        of score. If end_time is not specified, passage moved continues to
        end of score. If neither are specified, entire score is moved.
        """
        # TODO add parameter to overwrite existing music when displacing
        if displacement == 0:
            return
        if apply_to_existing_voices:
            voices = self.voices + self.existing_voices
        else:
            voices = self.voices
        for voice in voices:
            voice.displace_passage(displacement, start_time, end_time)

        for msg in self.meta_messages:
            # TODO don't move tempo changes past beginning of passage
            if start_time and msg.time < start_time:
                continue
            if end_time and msg.time >= end_time:
                continue
            msg.time = max(msg.time + displacement, 0)

    def remove_passage(
        self, start_time, end_time=0, apply_to_existing_voices=False
    ):
        """Removes from the specified start time until the specified end time.

        If end time is 0, then removes until the end of the Score.
        """
        # TODO debug, etc.
        # TODO what to do about overlapping durations?

        if apply_to_existing_voices:
            voice_lists = (self.voices, self.existing_voices)
        else:
            voice_lists = (self.voices,)
        for voice_list in voice_lists:
            for voice in voice_list:
                to_remove = []
                for attack in voice.data:
                    if attack < start_time:
                        continue
                    if end_time != 0 and attack >= end_time:
                        continue
                    to_remove.append(attack)
                for attack in to_remove:
                    del voice.data[attack]

    def repeat_passage(
        self,
        original_start_time,
        original_end_time,
        repeat_start_time,
        apply_to_existing_voices=False,
    ):
        """Repeats a passage."""
        if apply_to_existing_voices:
            voices = self.voices + self.existing_voices
        else:
            voices = self.voices
        for voice in voices:
            voice.repeat_passage(
                original_start_time, original_end_time, repeat_start_time
            )
        # TODO handle meta messages?

    def transpose(
        self, interval, start_time, end_time, apply_to_existing_voices=False
    ):
        for voice in self.voices:
            voice.transpose(interval, start_time, end_time)
        if apply_to_existing_voices:
            for voice in self.existing_voices:
                voice.transpose(interval, start_time, end_time)

    def get_note_attribute_names(self):
        """Returns the names of note attributes (so I don't have to
        manually update these anywhere).

        It's assumed that all note objects have the same attributes.

        Raises an ValueError if score is empty."""
        for voice in self:
            for note in voice:
                return list(vars(note).keys())
        raise ValueError(
            "It appears that the score doesn't contain " "any notes."
        )

    # def to_np(self, add_release_times=True):
    #     """Returns a np array of notes and a dict of column names: indexes.
    #
    #     The array will be sorted by attack_time, then voice, then choir,
    #     then pitch.
    #
    #     Keyword args:
    #         add_release_times: whether the array should include a column
    #             of release times.
    #
    #     Returns:
    #         tuple of np array, dict
    #
    #     Raises:
    #         ValueError: if score contains no notes.
    #     """
    #
    #     cols = self.get_note_attribute_names()
    #     if add_release_times:
    #         cols.append("release_time")
    #         cols_to_sort_by = (
    #             "attack_time",
    #             "voice",
    #             "choir",
    #             "pitch",
    #             "release_time",
    #         )
    #     else:
    #         cols_to_sort_by = ("attack_time", "voice", "choir", "pitch")
    #
    #     for col in reversed(cols_to_sort_by):
    #         cols.remove(col)
    #         cols.insert(0, col)
    #
    #     cols = {col: col_i for col_i, col in enumerate(cols)}
    #
    #     n_cols = len(cols)
    #     n_rows = sum([len(voice) for voice in self.voices])
    #     out_array = np.empty((n_rows, n_cols))
    #     row_i = 0
    #     for voice in self.voices:
    #         for note in voice:
    #             for col, col_i in cols.items():
    #                 try:
    #                     val = vars(note)[col]
    #                 except KeyError:
    #                     continue
    #                 out_array[row_i, col_i] = val  # np.float()
    #             row_i += 1
    #
    #     if add_release_times:
    #         out_array[:, cols["release_time"]] = out_array[
    #             :, [cols["attack_time"], cols["dur"]]
    #         ].sum(axis=1)
    #
    #     for col_i in range(len(cols_to_sort_by), 0, -1):
    #         kind = "quicksort" if col_i == len(cols_to_sort_by) else "mergesort"
    #         out_array = out_array[out_array[:, col_i - 1].argsort(kind=kind)]
    #
    #     return out_array, cols

    def get_passage(
        self,
        passage_start_time=None,
        passage_end_time=None,
        dont_overlap_start=True,
        end_time_refers_to_attack=True,
    ):
        """Returns all voices of a given passage as a Score object.

        Passage is inclusive of passage_start_time and exclusive of
        passage_end_time.

        Keyword args:
            passage_start_time: time for passage to begin. If None, then
                takes all notes until passage_end_time. Default None.
            passage_end_time: time for passage to end. If None, then takes all
                notes after passage_start_time. Default None.
            dont_overlap_start: bool. If True, then passage only includes note
                attacked after passage_start_time. If False, also includes
                notes attacked before passage_start_time, but still sounding
                at passage_start_time. Default True.
            end_time_refers_to_attack: bool. If True, then notes that start
                before passage_end_time are included. If False, then notes that
                *end* before passage_end_time (inclusive) are included. Default True.
        """
        passage = Score(
            tet=self.tet, harmony_times_dict=self.harmony_times_dict
        )
        for voice in self.voices:
            new_voice = voice.get_passage(
                passage_start_time=passage_start_time,
                passage_end_time=passage_end_time,
                dont_overlap_start=dont_overlap_start,
                end_time_refers_to_attack=end_time_refers_to_attack,
            )
            passage.add_voice(
                new_voice, voice_i=voice.voice_i, voice_range=voice.range
            )

        first_tempo_msg_after_passage_start = None
        for msg in self.meta_messages:
            # Meta messages have no duration so we don't need to consider
            #   dont_overlap_start.
            if passage_start_time is not None and msg.time < passage_start_time:
                if msg.type == "set_tempo":
                    last_tempo_msg_before_passage_start = msg
                continue
            if passage_end_time is not None and msg.time >= passage_end_time:
                continue
            if (
                msg.type == "set_tempo"
                and first_tempo_msg_after_passage_start is None
            ):
                first_tempo_msg_after_passage_start = msg
            passage.add_meta_message(copy.deepcopy(msg))
        if passage_start_time is None:
            return passage

        if (
            first_tempo_msg_after_passage_start is None
            or first_tempo_msg_after_passage_start.time > passage_start_time
        ):
            try:
                tempo_msg = copy.deepcopy(last_tempo_msg_before_passage_start)
                tempo_msg.time = passage_start_time
                passage.add_meta_message(tempo_msg)
            except NameError:
                pass

        return passage

    def get_harmony_times(self, harmony_i):
        return self.harmony_times_dict[harmony_i]

    def get_harmony_i(self, attack_time):
        """If passed an attack time beyond the end of the harmonies, will
        return the last harmony.
        """
        for harmony_i in self.harmony_times_dict:
            try:
                if (
                    self.harmony_times_dict[harmony_i + 1].start_time
                    > attack_time
                ):
                    return harmony_i
            except KeyError:
                return harmony_i

    def get_sounding_pitches(
        self, attack_time, dur=0, voices="all", min_attack_time=0, min_dur=0
    ):

        sounding_pitches = set()

        if voices == "all":
            # voices = [voice_i for voice_i in range(self.num_voices)]
            voices = self.all_voice_is

        for voice_i in voices:
            voice = self.voices[voice_i]
            sounding_pitches.update(
                voice.get_sounding_pitches(
                    attack_time,
                    dur=dur,
                    min_attack_time=min_attack_time,
                    min_dur=min_dur,
                )
            )

        for existing_voice in self.existing_voices:
            # Existing voices are always retrieved.
            sounding_pitches.update(
                existing_voice.get_sounding_pitches(
                    attack_time,
                    dur=dur,
                    min_attack_time=min_attack_time,
                    min_dur=min_dur,
                )
            )

        return list(sorted(sounding_pitches))

    def get_simultaneously_attacked_pitches(
        self, attack_time, voices="all", min_dur=0
    ):
        return self.get_sounding_pitches(
            attack_time,
            voices=voices,
            min_attack_time=attack_time,
            min_dur=min_dur,
        )

    def get_all_pitches_attacked_during_duration(
        self, attack_time, dur, voices="all"
    ):
        return self.get_sounding_pitches(
            attack_time, dur=dur, voices=voices, min_attack_time=attack_time
        )

    def get_all_pitches_sounding_during_duration(
        self, attack_time, dur, voices="all", min_dur=0
    ):
        return self.get_sounding_pitches(
            attack_time, dur=dur, voices=voices, min_dur=min_dur
        )

    def get_prev_n_pitches(
        self, n, time, voice_i, min_attack_time=0, stop_at_rest=False
    ):
        """Returns previous n pitches (attacked before time).

        If pitches are attacked earlier than min_attack_time, -1 will be
        returned instead.
        """
        return self.voices[voice_i].get_prev_n_pitches(
            n, time, min_attack_time=min_attack_time, stop_at_rest=stop_at_rest
        )

    def get_prev_pitch(
        self, time, voice_i, min_attack_time=0, stop_at_rest=False
    ):
        """Returns previous pitch from voice."""
        return self.voices[voice_i].get_prev_n_pitches(
            1, time, min_attack_time=min_attack_time, stop_at_rest=stop_at_rest
        )[0]

    def get_last_n_pitches(
        self, n, time, voice_i, min_attack_time=0, stop_at_rest=False
    ):
        """Returns last n pitches (including pitch attacked at time)."""
        return self.voices[voice_i].get_prev_n_pitches(
            n,
            time,
            min_attack_time=min_attack_time,
            stop_at_rest=stop_at_rest,
            include_start_time=True,
        )

    def _build_harmony_times_dict(self, harmony_len, total_len=None):
        class HarmonyTimesDictError(Exception):
            pass

        if total_len is None:
            raise HarmonyTimesDictError(
                "Must pass total_len with harmony_len when creating "
                "Score object."
            )

        self.harmony_times_dict = {}
        harmony_i = 0
        start_time = 0
        end_time = 0
        while True:
            end_time += harmony_len[harmony_i % len(harmony_len)]
            self.harmony_times_dict[harmony_i] = HarmonyTimes(
                start_time, end_time
            )
            # self.harmony_times_dict[harmony_i] = (start_time, end_time)
            start_time = end_time
            harmony_i += 1
            if end_time > total_len:
                break

    @property
    def all_voice_is(self):
        return [i for i in range(self.voices.num_new_voices)] + [
            i + self.voices.num_new_voices + 1
            for i in range(self.voices.num_existing_voices)
        ]

    def get_tempo_changes_from_meta_messages(self, coerce_=float):
        """Get the tempo changes.

        Keyword args:
            coerce_: type to coerce the tempo change times to. (Tempos
                themselves are floats.)

        Returns:
            A list of 2-tuples of form (tempo, tempo change time).
        """
        out = []
        for msg in self.meta_messages:
            if msg.type == "set_tempo":
                out.append((mido.tempo2bpm(msg.tempo), coerce_(msg.time)))
        return out

    def __init__(
        self,
        num_voices=0,
        tet=12,
        harmony_len=None,
        harmony_times_dict=None,
        total_len=None,
        ranges=(None,),
        time_sig=None,
        existing_score=None,
    ):

        if harmony_times_dict:
            self.harmony_times_dict = harmony_times_dict
        elif harmony_len:
            self._build_harmony_times_dict(harmony_len, total_len=total_len)
        else:
            self.harmony_times_dict = None
        self.tet = tet
        # self.speller = spell.Speller(tet)
        self.existing_voices = []
        if existing_score:
            for voice in existing_score.voices:
                self.existing_voices.append(voice)
            self.voices = VoiceList(
                # num_new_voices=num_voices,
                existing_voices=self.existing_voices
            )
        else:
            self.voices = VoiceList()  # num_new_voices=num_voices)
        self.meta_messages = []
        self.n_since_chord_tone_list = []
        self.num_voices = 0
        self.time_sig = time_sig
        self.attacks_adjusted_by = 0

        for i in range(num_voices):
            self.add_voice(voice_range=ranges[i % len(ranges)])
