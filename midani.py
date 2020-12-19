import argparse
import ast
import os
import re
import sys

import from_my_other_projects.midi_funcs as midi_funcs

import midani_av
import midani_misc_classes
import midani_plot
import midani_settings
import midani_time

NO_PATH_MSG = """Nothing to animate! Either
    - pass path to a midi file as a command-line argument with "-m" or "--midi"
    - include path to a midi file as "midifname" in a settings file passed with
        "-s" or "--settings\""""


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


def main(midi_path, audio_path, test_flag, user_settings_path):
    if user_settings_path is None:
        user_settings = {}
    else:
        with open(user_settings_path, "r", encoding="utf-8") as inf:
            user_settings = ast.literal_eval(inf.read())
    if midi_path is None:
        if "midifname" not in user_settings or not user_settings["midifname"]:
            print(NO_PATH_MSG)
            sys.exit(1)
    else:
        user_settings["midifname"] = midi_path
        if audio_path is None:
            user_settings["audio_fname"] = ""
    if audio_path is not None:
        user_settings["audio_fname"] = audio_path
    if test_flag:
        if "frame_increment" in user_settings:
            user_settings["frame_increment"] = max(
                [0.5, user_settings["frame_increment"]]
            )
        else:
            user_settings["frame_increment"] = 0.5
    settings = midani_settings.Settings(**user_settings)
    if settings.process_video != "only":
        score = read_score(settings)
        tempo_changes = midani_time.TempoChanges(score)
        settings.update_from_score(score, tempo_changes)
        score = crop_score(score, settings, tempo_changes)
        pitch_table = midani_misc_classes.PitchTable(
            score, settings, tempo_changes
        )
        n_frames = midani_plot.plot(settings, pitch_table)
    else:
        png_pattern = re.compile(
            os.path.basename(settings.png_fname_base) + r"\d+\.png"
        )
        n_frames = len(
            [
                f
                for f in os.listdir(settings.output_dirname)
                if re.match(png_pattern, f)
            ]
        )
    if settings.process_video != "no":
        midani_av.process_video(settings, n_frames)

        if settings.audio_fname:
            midani_av.add_audio(settings)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--midi", help="path to midi file to animate")
    parser.add_argument(
        "-a", "--audio", help="path to audio file to add to video"
    )
    parser.add_argument(
        "-s",
        "--settings",
        help="path to settings file containing a Python dictionary",
    )
    parser.add_argument(
        "-t",
        "--test",
        help="set frame rate to a maximum of 2 fps",
        action="store_true",
    )
    args = parser.parse_args()
    main(args.midi, args.audio, args.test, args.settings)
