"""Test that tempo change conversions in midani_time.py are working
"""
import dataclasses
import os
import sys
import traceback

import mido

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import src.midani_score as midani_score  # pylint: disable=wrong-import-position
import src.midani_time as midani_time  # pylint: disable=wrong-import-position

SCRIPT_PATH = os.path.dirname((os.path.realpath(__file__)))
OUT_DIR = os.path.join(SCRIPT_PATH, "test_mid")
OUT_PATH = os.path.join(OUT_DIR, "tempo_changes.mid")
TEMPOS = [120, 144, 160, 176]


@dataclasses.dataclass
class DummySettings:  # pylint: disable=missing-class-docstring
    midi_fname: tuple
    tet: int = 12
    midi_tracks_to_voices: bool = True
    midi_channels_to_voices: bool = False
    midi_reset_start_to_0: bool = False


def test_tempo_changes():
    mid = mido.MidiFile()
    meta_track = mido.MidiTrack()
    track = mido.MidiTrack()
    mid.tracks.extend([meta_track, track])
    ticks_per_beat = mid.ticks_per_beat
    # Add sixteen quarter notes
    for i in range(10):
        track.append(mido.Message("note_on", note=60 + i, time=0))
        track.append(mido.Message("note_off", note=60 + i, time=ticks_per_beat))

    # Add tempo changes every 2.5 beats
    for i, tempo in enumerate(TEMPOS):
        meta_track.append(
            mido.MetaMessage(
                "set_tempo",
                tempo=mido.bpm2tempo(tempo),
                time=int(ticks_per_beat * 2.5 if i != 0 else 0),
            )
        )

    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)
    mid.save(OUT_PATH)

    settings = DummySettings((OUT_PATH,))
    score = midani_score.read_score(settings)
    tempo_changes = midani_time.TempoChanges(score)
    times = [
        0,
        0.5,
        1.0,
        1.4583333333333333,
        1.875,
        2.291666666666667,
        2.666666666666667,
        3.041666666666667,
        3.3996212121212124,
        3.740530303030303,
    ]
    try:
        for note, time in zip(score.voices[0], times):
            # Times do not agree exactly because tempos don't come out exactly
            # from mido conversion (e.g., 144 becomes 143.99988480009216)
            assert (
                abs(time - tempo_changes.ctime_from_btime(note.attack_time))
                < 1e-6
            ), "abs(time - tempo_changes.ctime_from_btime(note.attack_time)) >= 1e-6"
    except:  # pylint: disable=bare-except
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()

    # t1 = 60 / 120
    # t2 = 60 / 144
    # t3 = 60 / 160
    # t4 = 60 / 176
    # beat_durs = [60 / t for t in TEMPOS]
    #
    # print(0)
    # print(t1 * 1)
    # print(t1 * 2)
    # print(t1 * 2.5 + t2 * 0.5)
    # print(t1 * 2.5 + t2 * 1.5)
    # print(t1 * 2.5 + t2 * 2.5)
    # print(t1 * 2.5 + t2 * 2.5 + t3 * 1)
    # print(t1 * 2.5 + t2 * 2.5 + t3 * 2)
    # print(t1 * 2.5 + t2 * 2.5 + t3 * 2.5 + t4 * 0.5)
    # print(t1 * 2.5 + t2 * 2.5 + t3 * 2.5 + t4 * 1.5)


if __name__ == "__main__":
    test_tempo_changes()
