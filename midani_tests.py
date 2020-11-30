import sys
import traceback

import midani_settings
import midani


def test_settings():
    # TODO replace with a shorter file
    MIDI_FNAME = "/Users/Malcolm/Music/Logic/efficient_rhythms_2/efficient_rhythms2_2522/efficient_rhythms2_2522_240.mid"
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
    # MIDI_FNAME = "/Users/Malcolm/Music/Logic/efficient_rhythms_2/efficient_rhythms2_2522/efficient_rhythms2_2522_240.mid"
    MIDI_FNAME = "/Users/Malcolm/Google Drive/python/efficient_rhythms2/efficient_rhythms2_midi/efficient_rhythms2_2207.mid"
    try:
        settings = midani_settings.Settings(
            MIDI_FNAME,
            clean_up_r_files=True,
            frame_len=5,
            frame_increment=1 / 10,
            intro=0,
            start_time=0,
            end_time=8,
            outro=0,
            process_video="yes",
            shadow_positions=[(-5, -5)],
            max_flutter_size=0,
            min_flutter_size=0,
            note_start=0.5,
            note_end=0.5,
            shadow_scale=1,
        )
        midani.main(settings)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        traceback.print_exception(
            exc_type, exc_value, exc_traceback, file=sys.stdout
        )
        breakpoint()


if __name__ == "__main__":
    # test_settings()
    test_main()
