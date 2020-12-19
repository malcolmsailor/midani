import sys
import traceback

import midani_settings
import midani_time
import midani

MIDI_FNAME = "sample_music/effrhy_2207.mid"


def test_settings():
    try:
        # I've changed Settings since writing these tests so they won't work
        # until they are updated
        A = midani_settings.Settings(MIDI_FNAME)
        B = midani_settings.Settings(MIDI_FNAME)
        assert A.p_displace is not B.p_displace, (
            "A.p_displace " "is not B.p_displace"
        )
        A = midani_settings.Settings(
            MIDI_FNAME, p_displace={-12: (11, 12, 13, 14), 10: (6, 7)}
        )
        for k, v in A.p_displace.items():
            for d in v:
                assert A.p_displace_rev[d] == k, "A.p_displace_rev[d] " "!= "
        for k, v in A.p_displace_rev.items():
            assert k in A.p_displace[v], "k " "not in A.p_displace[v]"
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


def test_main():
    MIDI_FNAME = "/Users/Malcolm/Google Drive/python/efficient_rhythms2/efficient_rhythms2_midi/efficient_rhythms2_2207.mid"
    AUDIO_FNAME = "/Users/Malcolm/Google Drive/python/efficient_rhythms2/efficient_rhythms2_midi/efficient_rhythms2_2207.mp3"
    try:
        # settings = midani_settings.Settings(
        #     MIDI_FNAME,
        #     audio_fname=AUDIO_FNAME,
        #     frame_len=2,
        #     frame_increment=1 / 5,
        #     intro=2,
        #     start_time=0,
        #     final_bar=2,
        #     final_beat=1,
        #     bar_length=4,
        #     end_time=0,
        #     outro=0,
        #     clean_up_r_files=False,
        #     # process_video="only",
        #     # shadow_positions=[(-5, -5), (-10, -10), (-15, -15), (-20, -20)],
        #     # shadow_gradients=True,
        #     # shadow_scale=0.9,
        #     global_connection_lines=False,
        #     # bounce_type="scalar",
        #     # bounce_size=1.2,
        #     # bounce_len=3,
        #     # bounce_period=0.4,
        #     # bg_beat_times_length=8,
        #     bg_beat_times_length=4,
        #     bg_beat_times=[1, 3,],
        #     intro_bg_color=(192, 32, 32),
        #     outro_bg_color=(32, 192, 32),
        #     bg_colors=[(32, 32, 32), (32, 32, 192)],
        #     # bg_color_blend=False,
        #     add_annotations=["time"],
        #     color_palette=[
        #         (41, 120, 142, 128),
        #         (72, 25, 107, 128),
        #         (210, 225, 27, 128),
        #         (34, 167, 132, 128),
        #         (121, 209, 81, 128),
        #         (165, 218, 53, 128),
        #         (30, 152, 138, 128),
        #         (56, 86, 139, 128),
        #         (68, 1, 84, 128),
        #         (83, 197, 103, 128),
        #         (64, 67, 135, 128),
        #         (48, 103, 141, 128),
        #         (35, 136, 141, 128),
        #         (70, 47, 124, 128),
        #         (253, 231, 36, 128),
        #         (53, 183, 120, 128),
        #     ],
        # )
        midani.main(settings)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


def process_settings(midifname, **kwargs):
    settings = midani_settings.Settings(midifname, **kwargs)
    score = midani.read_score(settings)
    tempo_changes = midani_time.TempoChanges(score)
    settings.update_from_score(score, tempo_changes)
    return settings


def test_bg_beat_times():
    # these tests assume that MIDI_FNAME has tempo of 120
    stings = process_settings(MIDI_FNAME, bg_beat_times_length=2)
    assert stings.bg_clock_times == [
        i for i in range(32)
    ], "stings.bg_clock_times != [i for i in range(32)]"
    stings = process_settings(
        MIDI_FNAME, bg_beat_times_length=2, bg_beat_times=[1,]
    )
    assert stings.bg_clock_times == [
        i + 0.5 for i in range(32)
    ], "stings.bg_clock_times != [i + 0.5 for i in range(32)]"


if __name__ == "__main__":
    test_bg_beat_times()
    # test_settings()
    # test_main()
