"""Provides TempoChanges class.
"""

import midani.from_my_other_projects.mal_misc as mal_misc


class TempoChanges:
    """Uses tempo changes from Score to convert between beats and clock times."""

    def __init__(self, score):
        self.t_changes_btimes = {
            beat: tempo
            for (tempo, beat) in score.get_tempo_changes_from_meta_messages()
        }
        self.beat_times = list(self.t_changes_btimes.keys())
        self.t_changes_ctimes = {}
        self.beat_time_to_clock_time = {}
        self.clock_time_to_beat_time = {}
        clock_time = 0
        prev_beat = 0
        for new_beat in self.beat_times:
            if new_beat == 0:
                pass
            else:
                clock_time += (
                    (new_beat - prev_beat)
                    * 60
                    / self.t_changes_btimes[prev_beat]
                )
            self.t_changes_ctimes[clock_time] = self.t_changes_btimes[new_beat]
            self.beat_time_to_clock_time[new_beat] = clock_time
            self.clock_time_to_beat_time[clock_time] = new_beat
            prev_beat = new_beat
        self.clock_times = list(self.t_changes_ctimes.keys())

    def ctime_from_btime(self, beat_time):
        tempo_btime = self.beat_times[
            mal_misc.binary_search(
                self.beat_times, beat_time, not_found="force_lower"
            )
        ]
        tempo = self.t_changes_btimes[tempo_btime]
        tempo_start = self.beat_time_to_clock_time[tempo_btime]
        beat_delta = beat_time - tempo_btime
        return tempo_start + beat_delta * 60 / tempo

    def btime_from_ctime(self, clock_time):
        tempo_ctime = self.clock_times[
            mal_misc.binary_search(
                self.clock_times, clock_time, not_found="force_lower"
            )
        ]
        tempo = self.t_changes_ctimes[tempo_ctime]
        tempo_start = self.clock_time_to_beat_time[tempo_ctime]
        clock_delta = clock_time - tempo_ctime
        return tempo_start + clock_delta * tempo / 60
