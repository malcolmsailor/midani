"""Tests for classes from midani_misc_classes.
"""
import os


from midani import midani_misc_classes


def test_flutter():
    for flutter_period in (1, 3, 4, 7):
        flutter = midani_misc_classes.PitchFlutter(
            max_flutter_size=4,
            min_flutter_size=1,
            max_flutter_period=flutter_period,
            min_flutter_period=flutter_period,
        )
        assert (
            abs(round(flutter(0), 10))
            == abs(round(flutter(flutter_period / 2), 10))
            == abs(round(flutter(flutter_period), 10))
        ), (
            "abs(round(flutter(0), 10)) != "
            f"abs(round(flutter({flutter_period / 2}), 10)) "
            f"!= abs(round(flutter({flutter_period}), 10))"
        )
        assert (
            flutter(0 - flutter.flutter_offset)
            < flutter(flutter_period / 8 - flutter.flutter_offset)
            < flutter(flutter_period / 4 - flutter.flutter_offset)
        ), (
            "flutter(0 - flutter.flutter_offset) "
            f">= flutter({flutter_period / 8} - flutter.flutter_offset) "
            f">= flutter({flutter_period / 4} - flutter.flutter_offset)"
        )


if __name__ == "__main__":
    print("=" * os.get_terminal_size().columns)
    test_flutter()
    print("=" * os.get_terminal_size().columns)
