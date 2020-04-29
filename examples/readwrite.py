"""Opens a stem file and saves (reencodes) back to a stem file
"""
import argparse
import stempeg
import numpy as np
from os import path as op


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'input',
    )
    args = parser.parse_args()

    # read stems
    stems, rate = stempeg.read_stems(args.input)
    print(stems.shape)
    stempeg.write_stems(stems, "test.stem.m4a")
    print(stempeg.Info("test.stem.m4a").nb_audio_streams)

    stems2, rate = stempeg.read_stems("test.stem.m4a")
    print(stems2.shape)
