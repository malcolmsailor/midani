"""Provides RBoss class to control Rscript.
"""

import contextlib
import os
import shutil
import subprocess

MAX_LINE_COUNT = 2000
MAX_PLOT_COUNT = 50
PLOT_PRINT_COUNT = 25
R_PRINT_COUNT = 1


class RBoss:
    """Class for writing R scripts and then calling Rscript to read them."""

    def __init__(self, settings):
        self.outfnumber = 0
        self.outf_dirname = settings._temp_r_dirname
        if not os.path.exists(self.outf_dirname):
            os.makedirs(self.outf_dirname)
        self.clean_up = settings.clean_up_r_files
        self.outfname_fmt_str = settings.temp_r_script_base
        self.outfnames = []
        self.plot_count = 0
        self._increment_outf()
        self.png_dirname = settings.output_dirname
        self.png_fname_base = settings.png_fname_base
        self.out_width = settings.out_width
        self.out_height = settings.out_height
        self._init_png_str = (
            f'png(file = "{self.png_fname_base}'
            f'{{png_fnumber:0{settings.png_fnum_digits}d}}.png", '
            f"width = {self.out_width}, height = {self.out_height})\n"
            # The next line is copied from the original version of the script,
            # I no longer remember what it does
            'par(mai = c(0,0,0,0), xaxs = "i", yaxs = "i")\n'
            'par(bg = "{bg_color}")\n'
            "plot(c({window_start}, {window_end}), "
            "c({window_bottom}, {window_top}), "
            'type = "n", xlab = "", ylab = "")\n'
        )

    @staticmethod
    def hex_color(color):
        # Will raise a ValueError if color has floats (rather than ints)
        return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}{color[3]:02x}"

    def _close_outf(self):
        try:
            self.outf.write("dev.off()\n")
            self.outf.close()
        except AttributeError:
            pass

    def _increment_outf(self):
        self._close_outf()
        self.outfname = self.outfname_fmt_str.format(self.outfnumber)
        self.outfnames.append(self.outfname)
        self.outfnumber += 1
        self.outf = open(self.outfname, "w")
        self.outf.write("require(grDevices)\n")
        self.line_count = 1

    @contextlib.contextmanager
    def make_png(self, window):
        self.init_png(window)
        try:
            yield
        finally:
            self.close_png()

    def init_png(self, window):
        if (
            self.line_count > MAX_LINE_COUNT
            or (self.plot_count + 1) % MAX_PLOT_COUNT == 0
        ):
            self._increment_outf()
        print(f"Writing frame {self.plot_count} \r", end="")
        self.outf.write(
            self._init_png_str.format(
                png_fnumber=self.plot_count + 1,
                bg_color=self.hex_color(window.bg_color),
                window_start=window.start,
                window_end=window.end,
                # The next lines are part of an abortive attempt to express
                # x coordinates in pixels, which I foolishly started before
                # committing other changes...
                # window_start=window.pixel_start,
                # window_end=window.pixel_end,
                window_bottom=window.bottom,
                window_top=window.top,
            )
        )
        self.line_count += 4

    def close_png(self):
        self.plot_count += 1

    def now_line(self, now, window):
        self.outf.write(
            f"lines(c({now, now}), c({window.bottom}, {window.top}))"
        )
        self.line_count += 1

    def plot_rect(self, x1, x2, y1, y2, color, zorder):
        self.outf.write(
            f'rect({x1}, {y1}, {x2}, {y2}, col = "{self.hex_color(color)}", '
            "border = NA)\n"
        )
        self.line_count += 1

    def plot_line(self, x1, x2, y1, y2, color, width, zorder):
        self.outf.write(
            f"lines(c({x1},{x2}), c({y1},{y2}), "
            f'col = "{self.hex_color(color)}", lwd = {width})\n'
        )
        self.line_count += 1

    def text(self, text, x, y, color, size, position=None, zorder=None):
        if position is None:
            adj = "NULL"
        else:
            adj = f"c{position}"
        self.outf.write(
            f'text(c({x}), c({y}), "{text}", '
            f'col = "{self.hex_color(color)}", cex={size}, adj={adj})\n'
        )
        self.line_count += 1

    def bracket(self, x1, x2, y1, y2, color, width, zorder):
        self.outf.write(
            f"lines(c({x1},{x1},{x2},{x2}), c({y1},{y2},{y2},{y1}), "
            f'col = "{self.hex_color(color)}", lwd = {width})\n'
        )
        self.line_count += 1

    def run(self):
        print(f"Plotting {self.plot_count} frames in R")
        if not os.path.exists(self.png_dirname):
            os.makedirs(self.png_dirname)
        self._close_outf()
        for count, outfname in enumerate(self.outfnames):
            if count % R_PRINT_COUNT == 0:
                print(
                    f"Processing R file {count + 1}/{self.outfnumber}  \r",
                    end="",
                )
            proc = subprocess.run(
                ["Rscript", outfname],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            if proc.returncode != 0:
                print("")
                print(f"Rscript returned error code {proc.returncode}")
                print(proc.stdout.decode())
        print("")
        if self.clean_up:
            print("Removing temporary R files")
            shutil.rmtree(self.outf_dirname)
