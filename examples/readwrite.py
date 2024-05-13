"""Opens a stem file and saves (re-encodes) back to a stem file
"""
import argparse
import stempeg
import subprocess as sp
import numpy as np
from os import path as op


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

    # load stems
    stems, rate = stempeg.read_stems(stempeg.example_stem_path())

    stems = {
        "mix": stems[0],
        "drums": stems[1],
        "bass": stems[2],
        "other": stems[3],
        "vocals": stems[4],
    }

    stempeg.write_stems(
        ("output", ".flac"),
        stems,
        sample_rate=rate,
        writer=stempeg.FilesWriter(
            output_sample_rate=44100,
            stem_names=["mix", "drums", "bass", "other", "vocals"]
        )
    )
