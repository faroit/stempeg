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
    stempeg.write_stems(stems, "stems.mp4")
    stems2, rate = stempeg.read_stems("stems.mp4")
    print(stems2.shape)
