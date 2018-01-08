import stempeg
import numpy as np


def test_shape():
    R = np.random.random((5, 4096, 2))
    stempeg.write_stems(R, "./random.stem.mp4")
    S, rate = stempeg.read_stems(
        "./random.stem.mp4"
    )

    assert S.shape == R.shape
