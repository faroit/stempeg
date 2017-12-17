import stempeg


def test_shape():
    S, rate = stempeg.read_stems(
        "tests/data/The Easton Ellises - Falcon 69.stem.mp4"
    )
    assert S.shape == (5, 265216, 2)

    stempeg.write_stems(S, "./stems.mp4")
    S_r, rate_r = stempeg.read_stems("./stems.mp4")
    assert S.shape == S_r.shape
