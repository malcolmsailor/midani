"""Functions for compiling video and adding audio.
"""
import os
import shutil
import subprocess
import tempfile

import cv2


def process_video(settings, n):
    # After http://tsaith.github.io/combine-images-into-a-video-with-python-3-and-opencv-3.html

    # For some reason, pylint doesn't recognize any of the members I
    # import from cv2
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # pylint: disable=no-member
    out = cv2.VideoWriter(  # pylint: disable=no-member
        settings.video_fname,
        fourcc,
        1 / settings.frame_increment,
        (settings.out_width, settings.out_height),
    )
    try:
        terminal_width = os.get_terminal_size().columns
    except OSError:  # Thrown when running with pytest
        terminal_width = 80
    if (
        len(settings.png_fname_base) + settings.png_fnum_digits + 11
        > terminal_width
    ):
        print_png = os.path.basename(settings.png_fname_base)
    else:
        print_png = settings.png_fname_base
    print(f"Building {settings.video_fname}...")
    for i in range(1, n):
        str_i = str(i).zfill(settings.png_fnum_digits)
        img_path = f"{settings.png_fname_base}{str_i}.png"
        print(f"\rAdding {print_png}{str_i}.png", end="")
        frame = cv2.imread(img_path)  # pylint: disable=no-member
        if frame is None:
            print(f"\nError: couldn't read {img_path}")
        elif settings.clean_up_png_files:
            os.remove(img_path)
        out.write(frame)
    print("\nDone.")

    out.release()
    cv2.destroyAllWindows()  # pylint: disable=no-member


def add_audio(settings):
    if not shutil.which("ffmpeg"):
        print("ffmpeg not found! Can't add audio to video.")
        return
    temp_file = os.path.join(
        tempfile.gettempdir(), os.path.basename(settings.video_fname)
    )
    proc = subprocess.run(
        [
            "ffmpeg",
            "-i",
            settings.video_fname,
            "-itsoffset",
            str(settings.intro),
            "-i",
            settings.audio_fname,
            "-c",
            "copy",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            temp_file,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if proc.returncode != 0:
        print(f"ffmpeg returned error code {proc.returncode}")
        print(proc.stdout.decode())
    else:
        print(f"Audio file {settings.audio_fname} added to video with ffmpeg")
    os.remove(settings.video_fname)
    shutil.move(temp_file, settings.video_fname)
