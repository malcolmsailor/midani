"""For annotating frames and adding lyrics.
"""


def time(window):
    return f"{window.now:f}"


def section(window):
    if window.in_intro:
        return "intro"
    if window.in_outro:
        return "outro"
    return "main"


ANNOT = {
    "time": time,
    "section": section,
}


class Lyricist:
    """Provides the lyrics at the current moment.
    """

    def __init__(self, settings):
        self.prev_time = self.prev_lyric = None
        try:
            self.lyrics = iter(
                sorted(settings.lyrics.items(), key=lambda x: x[0])
            )
        except AttributeError:
            self.lyrics = self.next_time = self.next_lyric = None
        else:
            self.next_time, self.next_lyric = next(self.lyrics)

    def _update(self, now=None):
        if self.next_time is None:
            return
        if now is not None:
            if now < self.next_time:
                return
        self.prev_time, self.prev_lyric = self.next_time, self.next_lyric
        try:
            self.next_time, self.next_lyric = next(self.lyrics)
        except StopIteration:
            self.next_time = self.next_lyric = None

    def __call__(self, now):
        self._update(now=now)
        return self.prev_lyric
