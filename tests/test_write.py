import stempeg
import pytest


def test_write():
    S, rate = stempeg.read_stems(stempeg.example_stem_path())
    stempeg.write_stems(S, "./stems.mp4")
