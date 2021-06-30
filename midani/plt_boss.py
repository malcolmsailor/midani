import contextlib

import matplotlib.lines as lines
import matplotlib.patches as patches
import matplotlib.pyplot as plt

import numpy as np


class MPLBoss:
    def __init__(self, settings):
        self.outf_dirname = settings._temp_r_dirname
        self.png_dirname = settings.output_dirname
        self.png_fname_base = (
            settings.png_fname_base
            + f"{{png_fnumber:0{settings.png_fnum_digits}d}}.png"
        )

        self.plot_count = 0
        # init private vars
        self._fig = self._ax = None
        # dpi more or less chosen arbitrarily; I'm not sure how important this
        # value is. Its purpose is to scale width and height (because mpl
        # understands these in terms of inches and dpi, rather than pixels.)
        # The actually realized size in pixels seems to be slightly smaller
        # than one would expect---e.g., I'm asking for 1280x720 and getting
        # 1270x710. I'm not sure what to do about this.
        self._dpi = 96

        self.out_width = settings.out_width / self._dpi
        self.out_height = settings.out_height / self._dpi

    @contextlib.contextmanager
    def make_png(self, window):
        self.init_png(window)
        try:
            yield
        finally:
            self.close_png(window)

    def init_png(self, window):
        print(f"Writing frame {self.plot_count} \r", end="")

        assert self._ax is None
        self._fig, self._ax = plt.subplots(
            figsize=(self.out_width, self.out_height), dpi=self._dpi
        )
        plt.axis("off")

        self._ax.set_xlim(window.start, window.end)
        self._ax.set_ylim(window.bottom, window.top)

    def close_png(self, window):
        png_fname = self.png_fname_base.format(png_fnumber=self.plot_count + 1)
        self._fig.tight_layout()
        # Infuriatingly, savefig overrides any value of facecolor set
        # previously
        self._fig.savefig(
            png_fname,
            dpi="figure",
            facecolor=self.hex_color(window.bg_color),
        )
        plt.close(self._fig)
        self._fig = self._ax = None
        self.plot_count += 1

    @staticmethod
    def hex_color(color):
        # Will raise a ValueError if color has floats (rather than ints)
        return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}{color[3]:02x}"

    def now_line(self, now, window):
        line = lines.Line2D([now, now], [window.bottom, window.top], zorder=30)
        self._ax.add_line(line)

    def plot_rect(self, x1, x2, y1, y2, color, zorder):
        rect = patches.Polygon(
            xy=np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]]),
            color=self.hex_color(color),
            zorder=zorder,
        )
        self._ax.add_patch(rect)

    def plot_line(self, x1, x2, y1, y2, color, width, zorder):
        # linewidth in matplotlib appears to be about twice as thick as the
        # corresponding value in R

        # The default zorder for patches is 1; for lines, 2. We want lines to
        # appear behind patches.

        line = lines.Line2D(
            [x1, x2],
            [y1, y2],
            color=self.hex_color(color),
            linewidth=width / 2,
            zorder=zorder,
        )
        self._ax.add_line(line)

    x_alignments = {0: "left", 0.5: "center", 1.0: "right"}
    y_alignments = {0: "baseline", 0.5: "center", 1.0: "top"}

    def text(self, text, x, y, color, size, position=(0.5, 0), zorder=20):
        # The "size" argument was originally used for the 'cex' argument of
        # r's text() function, which scales the text relative to some
        # baseline size. Eyeballing it, multiplying this by 8 seems to
        # give a similar size.
        ha = self.x_alignments[position[0]]
        va = self.y_alignments[position[1]]

        self._ax.text(
            x,
            y,
            text,
            color=self.hex_color(color),
            fontsize=8 * size,
            horizontalalignment=ha,
            verticalalignment=va,
            zorder=zorder,
        )

    def bracket(self, x1, x2, y1, y2, color, width, zorder):
        line = lines.Line2D(
            [x1, x1, x2, x2],
            [y1, y2, y2, y1],
            color=self.hex_color(color),
            linewidth=width / 2,
            zorder=zorder,
        )
        self._ax.add_line(line)

    def run(self):
        # This function exists for compatibility with the previous R version
        # of this class, but there is nothing to do here.
        pass
