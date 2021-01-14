"""Tests voice settings attribute access.
"""
import os
import sys
import traceback

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import src.midani_settings as midani_settings  # pylint: disable=wrong-import-position
import src.midani_score as midani_score  # pylint: disable=wrong-import-position
import src.midani_time as midani_time  # pylint: disable=wrong-import-position


SCRIPT_PATH = os.path.dirname((os.path.realpath(__file__)))


def test_voice_settings():
    settings_kwargs = {
        "midi_fname": os.path.join(
            SCRIPT_PATH, "../sample_music/effrhy_105.mid"
        ),
        "script_path": SCRIPT_PATH,
        "voice_settings": {
            0: {
                "note_start": 1,
                "note_end": 1.5,
                "bracket_settings": {
                    "1": {"line_width": 2.0, "x_offset": 1},
                    "2": {},
                },
                "default_bracket_settings": {"text_y_offset": 2},
            },
            1: {"note_start": 0},
        },
        "note_start": 0.5,
        "note_end": 2,
        "note_end_width": 2,
        "duplicate_voice_settings": {0: [1,]},
        "bracket_settings": {"1": {"line_width": 7}, "3": {"line_width": 0.5}},
        "default_bracket_settings": {"x_offset": 2, "text_y_offset": 1},
    }
    try:
        settings = midani_settings.Settings(**settings_kwargs)
        score = midani_score.read_score(settings)
        tempo_changes = midani_time.TempoChanges(score)
        settings.update_from_score(score, tempo_changes)
        assert (
            settings[1].note_end_width == settings.note_end_width
        ), "settings[1].note_end_width != settings.note_end_width"
        assert (
            settings[0].note_end_width == settings.note_end_width
        ), "settings[0].note_end_width != settings.note_end_width"
        assert (
            settings[1].frame_note_end == settings[0].frame_note_end
        ), "settings[1].frame_note_end != settings[0].frame_note_end"
        assert (
            settings[1].frame_note_end != settings.frame_note_end
        ), "settings[1].frame_note_end == settings.frame_note_end"
        assert (
            settings[1].frame_note_start != settings[0].frame_note_start
        ), "settings[1].frame_note_start == settings[0].frame_note_start"
        assert (
            settings[0].frame_note_start != settings.frame_note_start
        ), "settings[0].frame_note_start == settings.frame_note_start"
        assert (
            settings[0].bracket_settings["3"] is settings.bracket_settings["3"]
        ), (
            'settings[0].bracket_settings["3"] '
            'is not settings.bracket_settings["3"]'
        )
        assert (
            settings[0].bracket_settings["1"]
            is settings[1].bracket_settings["1"]
        ), (
            'settings[0].bracket_settings["1"] '
            'is not settings[1].bracket_settings["1"]'
        )
        assert (
            settings[0].bracket_settings["1"].line_width
            != settings.bracket_settings["1"].line_width
        ), (
            'settings[0].bracket_settings["1"].line_width '
            '== settings.bracket_settings["1"].line_width'
        )
        assert (  # This assertion will fail if I change the default value (5.0)
            settings[0].bracket_settings["2"].line_width == 5.0
        ), 'settings[0].bracket_settings["2"].line_width != 5.0'
        assert (
            settings[1].bracket_settings["2"].x_offset == 2
        ), 'settings[1].bracket_settings["2"].x_offset != 2'
        assert (
            settings[1].bracket_settings["1"].x_offset == 1
        ), 'settings[1].bracket_settings["1"].x_offset != 1'
        assert (
            settings[1].bracket_settings["2"].text_y_offset == 2
        ), 'settings[1].bracket_settings["2"].text_y_offset != 2'
    except:  # pylint: disable=bare-except
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


if __name__ == "__main__":
    test_voice_settings()
