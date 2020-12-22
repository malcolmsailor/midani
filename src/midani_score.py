"""Provides functions to read midi file into score object.
"""

import src.from_my_other_projects.midi_funcs as midi_funcs

def read_score(settings):
    return midi_funcs.read_midi_to_internal_data(
        settings.midifname,
        tet=settings.tet,
        split_tracks_to_voices=settings.midi_tracks_to_voices,
        split_channels_to_voices=settings.midi_channels_to_voices,
    )


def crop_score(score, settings, tempo_changes):
    start_beat = tempo_changes.btime_from_ctime(settings.start_time)
    end_beat = tempo_changes.btime_from_ctime(settings.end_time)
    return score.get_passage(
        passage_start_time=start_beat,
        passage_end_time=end_beat,
        end_time_refers_to_attack=True,
    )
