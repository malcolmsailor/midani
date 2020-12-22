"""Make piano-roll animations from midi files.
"""

import argparse
import ast
import os
import re
import sys

import src.midani_av as midani_av
import src.midani_plot as midani_plot
import src.midani_settings as midani_settings

NO_PATH_MSG = """Nothing to animate! Either
    - pass path to a midi file as a command-line argument with "-m" or "--midi"
    - include path to a midi file as "midifname" in a settings file passed with
        "-s" or "--settings\""""

ARGPARSE_DESCRIPTION = """Animate a midi file. The path to a midi file must
either be included as a command line argument with -m/--midi, or it must be
specified with the "midifname" keyword argument in a settings file provided with
-s/--settings."""

SCRIPT_PATH = os.path.dirname((os.path.realpath(__file__)))


def main(midi_path, audio_path, test_flag, user_settings_path):
    """Foo bar blah blah.
    """
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
    settings = midani_settings.Settings(
        script_path=SCRIPT_PATH, **user_settings
    )
    if settings.process_video != "only":
        n_frames = midani_plot.plot(settings)
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

        print(f"The output file is\n{settings.video_fname}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=ARGPARSE_DESCRIPTION)
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
