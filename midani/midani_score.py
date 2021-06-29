"""Provides functions to read midi file into score object.
"""

import midani.from_my_other_projects.midi_funcs as midi_funcs


def read_score(settings):
    def _read(midi_fname):
        return midi_funcs.read_midi_to_internal_data(
            midi_fname,
            tet=settings.tet,
            first_note_at_0=settings.midi_reset_start_to_0,
            split_tracks_to_voices=settings.midi_tracks_to_voices,
            split_channels_to_voices=settings.midi_channels_to_voices,
        )

    score = _read(settings.midi_fname[0])
    for midi_fname in settings.midi_fname[1:]:
        new_score = _read(midi_fname)
        for voice in new_score.voices:
            score.add_voice(voice, voice_i=score.num_voices)
    return score


def crop_score(score, settings, tempo_changes):
    start_beat = tempo_changes.btime_from_ctime(settings.start_time)
    end_beat = tempo_changes.btime_from_ctime(settings.end_time)
    return score.get_passage(
        passage_start_time=start_beat,
        passage_end_time=end_beat,
        end_time_refers_to_attack=True,
    )
