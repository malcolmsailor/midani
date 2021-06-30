"""Write pngs with midani_plot.py to verify it is working as expected.
"""

import os
import sys

from midani import midani_plot
from midani import midani_settings

SCRIPT_PATH = os.path.dirname((os.path.realpath(__file__)))
OUT_PATH = os.path.join(SCRIPT_PATH, "test_out/pngs")


def test_plot():

    settings = midani_settings.Settings(
        midi_fname=os.path.join(
            SCRIPT_PATH, "..", "sample_music", "effrhy_732.mid"
        ),
        script_path=SCRIPT_PATH,
        output_dirname=OUT_PATH,
        intro=0,
        start_time=0,
        end_time=1,
        outro=0,
    )
    midani_plot.plot(settings, False)
    print(f"Wrote test pngs to folder {OUT_PATH}")


if __name__ == "__main__":
    print("=" * os.get_terminal_size().columns)
    test_plot()
    print("=" * os.get_terminal_size().columns)
