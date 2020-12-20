import dataclasses
import os
import shutil
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import src.midani_av as midani_av  # pylint: disable=wrong-import-position

SCRIPT_PATH = os.path.dirname((os.path.realpath(__file__)))
OUT_PATH = os.path.join(SCRIPT_PATH, "test_out")


@dataclasses.dataclass
class DummySettings:
    png_fnum_digits: int = 5
    frame_increment: float = 1 / 30
    video_fname: str = os.path.join(OUT_PATH, "test_video.mp4")
    out_width: int = 1280
    out_height: int = 720
    png_fname_base: str = os.path.join(SCRIPT_PATH, "test_pngs/effrhy_732")
    clean_up_png_files: bool = False
    intro: float = 0.0
    audio_fname: str = os.path.join(SCRIPT_PATH, "test_audio/effrhy_732.mp3")


def test_video():
    print("Running test_video()")
    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)
    settings = DummySettings()
    if os.path.exists(settings.video_fname):
        os.remove(settings.video_fname)
    midani_av.process_video(settings, 31)
    print(f"test_video() output is in {settings.video_fname}")


def test_audio():
    print("Running test_audio()")
    if not os.path.exists(OUT_PATH):
        os.makedirs(OUT_PATH)

    out_path = os.path.join(OUT_PATH, "test_audio.mp4")
    if os.path.exists(out_path):
        os.remove(out_path)
    shutil.copy(
        os.path.join(SCRIPT_PATH, "test_video/test_video.mp4"), out_path
    )
    settings = DummySettings(video_fname=out_path)
    midani_av.add_audio(settings)
    print(f"test_audio() output is in {settings.video_fname}")


if __name__ == "__main__":
    print("=" * os.get_terminal_size().columns)
    test_video()
    print("=" * os.get_terminal_size().columns)
    test_audio()
    print("=" * os.get_terminal_size().columns)
