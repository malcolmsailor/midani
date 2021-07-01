"""Misc tests for midani
"""
import os
import sys

from midani import midani_score
from midani import midani_settings
from midani import midani_time

SCRIPT_PATH = os.path.dirname((os.path.realpath(__file__)))


def test_bg_beat_times():
    midi_fname = "../sample_music/effrhy_2207.mid"
    settings_kwargs = {
        "midi_fname": os.path.join(SCRIPT_PATH, midi_fname),
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
