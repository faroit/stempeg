import os
import stempeg
import pytest


def test_shape():
    S, rate = stempeg.read_stems(
        "tests/data/The Easton Ellises - Falcon 69.stem.mp4"
    )
    assert S.shape == (5, 265216, 2)
