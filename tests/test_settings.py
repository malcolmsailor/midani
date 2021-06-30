"""Some tests for midani_settings.
"""
import random
import os


from midani import midani_settings
from midani import midani_score
from midani import midani_time


SCRIPT_DIR = os.path.dirname((os.path.realpath(__file__)))


def test_read_settings_files_into_dict():
    settings_paths = (
        "tests/test_settings/multiple_settings1.py",
        "tests/test_settings/multiple_settings2.py",
    )
    out_dict = midani_settings.read_settings_files_into_dict(
        settings_paths, False
    )

    assert out_dict["intro"] == 5, 'out_dict["intro"] != 5'
    assert (
        out_dict["voice_settings"][1]["color_loop"] == 2
    ), 'out_dict["voice_settings"][1]["color_loop"] != 2'
    for key, val in (
        ("color_loop", 4),
        ("connection_lines", False),
        ("line_start", 0.4),
    ):
        assert (
            out_dict["voice_settings"][0][key] == val
        ), 'out_dict["voice_settings"][0][key] != val'


def test_voice_settings():
    settings_kwargs = {
        "midi_fname": os.path.join(
            SCRIPT_DIR, "../sample_music/effrhy_105.mid"
        ),
        "script_path": SCRIPT_DIR,
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
        "duplicate_voice_settings": {
            0: [
                1,
            ]
        },
        "bracket_settings": {"1": {"line_width": 7}, "3": {"line_width": 0.5}},
        "default_bracket_settings": {"x_offset": 2, "text_y_offset": 1},
    }

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
        settings[0].bracket_settings["1"] is settings[1].bracket_settings["1"]
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


def test_voice_order():
    # This test might seem trivial but weird stuff is going on so I wanted
    #   to double-check
    midi_fname = os.path.join(SCRIPT_DIR, "../sample_music/effrhy_105.mid")
    for _ in range(2):
        voice_order = list(range(16))  # Number of tracks in effrhy_105
        random.shuffle(voice_order)
        settings_dict = {
            "midi_fname": midi_fname,
            "voice_order": voice_order,
            "script_path": SCRIPT_DIR,
        }
        settings = midani_settings.Settings(**settings_dict)
        score = midani_score.read_score(settings)
        tempo_changes = midani_time.TempoChanges(score)
        settings.update_from_score(score, tempo_changes)
        assert (
            voice_order == settings.voice_order
        ), "voice_order != settings.voice_order"
        settings_dict["voice_order_reverse"] = True
        settings = midani_settings.Settings(**settings_dict)
        score = midani_score.read_score(settings)
        tempo_changes = midani_time.TempoChanges(score)
        settings.update_from_score(score, tempo_changes)
        voice_order.reverse()
        assert (
            voice_order == settings.voice_order
        ), "voice_order != settings.voice_order"


if __name__ == "__main__":
    test_read_settings_files_into_dict()
    test_voice_settings()
    test_voice_order()
