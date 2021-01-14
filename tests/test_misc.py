"""Misc tests for midani
"""
import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import src.midani_score as midani_score  # pylint: disable=wrong-import-position
import src.midani_settings as midani_settings  # pylint: disable=wrong-import-position
import src.midani_time as midani_time  # pylint: disable=wrong-import-position

SCRIPT_PATH = os.path.dirname((os.path.realpath(__file__)))


def test_bg_beat_times():
    midi_fname = "../sample_music/effrhy_2207.mid"
    settings_kwargs = {
        "midi_fname": os.path.join(SCRIPT_PATH, midi_fname),
        "script_path": SCRIPT_PATH,
        "bg_beat_times_length": 2,
    }
    settings = midani_settings.Settings(**settings_kwargs)
    score = midani_score.read_score(settings)
    tempo_changes = midani_time.TempoChanges(score)
    assert (
        len(tempo_changes.t_changes_btimes) == 1
    ), "len(tempo_changes.t_changes_btimes) != 1"
    assert (
        tempo_changes.t_changes_btimes[0.0] == 120.0
    ), "tempo_changes.t_changes_btimes[0.0] != 120.0"
    settings.update_from_score(score, tempo_changes)
    assert settings.bg_clock_times == list(
        range(33)
    ), "settings.bg_clock_times != list(range(33))"
    settings_kwargs["bg_beat_times_length"] = 2
    settings_kwargs["bg_beat_times"] = [
        1,
    ]
    settings = midani_settings.Settings(**settings_kwargs)
    score = midani_score.read_score(settings)
    tempo_changes = midani_time.TempoChanges(score)
    settings.update_from_score(score, tempo_changes)
    assert settings.bg_clock_times == [
        i + 0.5 for i in range(33)
    ], "settings.bg_clock_times != [i + 0.5 for i in range(33)]"


if __name__ == "__main__":
    test_bg_beat_times()