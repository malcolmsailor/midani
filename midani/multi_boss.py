"""This class was for testing/comparing RBoss and MPLBoss. Keeping it around in
case that is ever useful again.
"""
import contextlib

from .plt_boss import MPLBoss
from .midani_r import RBoss


class MultiBoss:
    def __init__(self, settings):
        self.rboss = RBoss(settings)
        self.plot_boss = MPLBoss(settings)

    @contextlib.contextmanager
    def make_png(self, *args):
        self.rboss.init_png(*args)
        self.plot_boss.init_png(*args)
        try:
            yield
        finally:
            self.rboss.close_png()
            self.plot_boss.close_png(*args)
            self.plot_count = self.plot_boss.plot_count

    def now_line(self, *args, **kwargs):
        self.rboss.now_line(*args, **kwargs)
        self.plot_boss.now_line(*args, **kwargs)

    def plot_rect(self, *args, **kwargs):
        self.rboss.plot_rect(*args, **kwargs)
        self.plot_boss.plot_rect(*args, **kwargs)

    def plot_line(self, *args, **kwargs):
        self.rboss.plot_line(*args, **kwargs)
        self.plot_boss.plot_line(*args, **kwargs)

    def text(self, *args, **kwargs):
        self.rboss.text(*args, **kwargs)
        self.plot_boss.text(*args, **kwargs)

    def bracket(self, *args, **kwargs):
        self.rboss.bracket(*args, **kwargs)
        self.plot_boss.bracket(*args, **kwargs)

    def run(self):
        self.rboss.run()
        self.plot_boss.run()
