import argparse
import os
import re
import shutil
import sys

from . import midani_av
from . import midani_plot
from . import midani_settings

NO_PATH_MSG = """Nothing to animate! Either
    - pass path to a midi file as a command-line argument with "-m" or "--midi"
    - include path to a midi file as "midi_fname" in a settings file passed with
        "-s" or "--settings\""""

ARGPARSE_DESCRIPTION = """Animate a midi file. The path to a midi file must
either be included as a command line argument with -m/--midi, or it must be
specified with the "midi_fname" keyword argument in a settings file provided with
-s/--settings."""


def parse_args():
    parser = argparse.ArgumentParser(description=ARGPARSE_DESCRIPTION)
    parser.add_argument("-m", "--midi", help="path to midi file to animate")
    parser.add_argument(
        "-a", "--audio", help="path to audio file to add to video"
    )
    parser.add_argument(
        "-s",
        "--settings",
        nargs="*",
        help="path to settings files, each containing a Python dictionary",
    )
    parser.add_argument(
        "-t",
        "--test",
        help="set frame rate to a maximum of 2 fps",
        action="store_true",
    )
    parser.add_argument(
        "-e",
        "--eval",
        help=(
            "use 'eval()' rather than 'ast.literal_eval()' to  parse settings. "
        ),
        action="store_true",
    )
    parser.add_argument(
        "-f",
        "--frames",
        help=(
            "a comma-separated list of numbers (with no spaces); specifies a "
            "list of individual frames to be drawn"
        ),
        type=get_frames,
        default=None,
    )
    parser.add_argument(
        "--mpl",
        help=("use matplotlib (rather than R) for plotting. Much slower."),
        action="store_true",
    )
    args = parser.parse_args()
    return (
        args.midi,
        args.audio,
        args.test,
        args.settings,
        args.eval,
        args.frames,
        args.mpl,
    )


def check_requirements(mpl):
    if not mpl:
        if not shutil.which("Rscript"):
            print(
                "ERROR: "
                "Can't find `Rscript` in path. Perhaps you need to install R?\n"
                "You can also plot with matplotlib using the --mpl argument.\n"
                "However, matplotlib seems to be much slower."
            )
            sys.exit(1)
    else:
        try:
            import matplotlib  # pylint: disable=unused-import, import-outside-toplevel
        except ModuleNotFoundError:
            print(
                "ERROR: "
                "Can't import `matplotlib`. Perhaps you need to install it?\n"
                "However, be warned that this script is much slower when \n"
                "using matplotlib. Using `R` instead is recommended."
            )
            sys.exit(1)


def main():

    print("Midani: make piano-roll animations from midi files")
    print("==================================================")
    print("https://github.com/malcolmsailor/midani\n")
    (
        midi_path,
        audio_path,
        test_flag,
        user_settings_paths,
        use_eval,
        frame_list,
        mpl,
    ) = parse_args()
    if user_settings_paths is None:
        user_settings = {}
    else:
        user_settings = midani_settings.read_settings_files_into_dict(
            user_settings_paths, use_eval
        )
    if midi_path is None:
        if "midi_fname" not in user_settings or not user_settings["midi_fname"]:
            print(NO_PATH_MSG)
            sys.exit(1)
    else:
        user_settings["midi_fname"] = midi_path
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
        user_settings["_test"] = True
    settings = midani_settings.Settings(**user_settings)
    if settings.process_video != "only":
        check_requirements(mpl)
    if frame_list is not None or settings.process_video != "only":
        n_frames = midani_plot.plot(settings, mpl, frame_list)
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
    if frame_list is None and settings.process_video != "no":
        midani_av.process_video(settings, n_frames)

        if settings.audio_fname:
            midani_av.add_audio(settings)

        print(f"The output file is\n{settings.video_fname}")
    if frame_list is not None:
        print("The output files are:")
        for i in range(1, n_frames + 1):
            print(
                f"{settings.png_fname_base}"
                f"{str(i).zfill(settings.png_fnum_digits)}.png"
            )


def get_frames(in_str):
    bits = in_str.split(",")
    try:
        return tuple(float(bit) for bit in bits)
    except ValueError:
        sys.exit(
            "Fatal error: Didn't understand '--frames'/'-f' argument "
            f"'{in_str}'. Pass a comma separated list with no spaces, e.g., "
            "'--frames 0.25' or '--frames 2,4,6.5'"
        )


if __name__ == "__main__":
    main()
