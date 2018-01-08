import stempeg


def test_shape():
    S, rate = stempeg.read_stems(
        "tests/data/The Easton Ellises - Falcon 69.stem.mp4"
    )
    stempeg.write_stems(S, "./stems.mp4")
