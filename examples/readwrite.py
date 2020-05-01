"""Opens a stem file and saves (reëncodes) back to a stem file
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

    # load stems
    stems, rate = stempeg.read_stems(args.input)

    # load stems, resampled to 96000 Hz
    stems, rate = stempeg.read_stems(args.input, sample_rate=96000)

    # --> stems now has `shape=(stem x samples x channels)``

    # save stems as multi-stream mp4
    stempeg.write_stems(
        "test.stem.m4a",
        stems,
        sample_rate=96000
    )

    # `write_stems` is a preset for the following settings
    # here the output signal is resampled to 44100 Hz and AAC codec is used
    stempeg.write_streams(
        "test.stem.m4a",
        stems,
        codec="aac",
        bitrate="256000",
        sample_rate=96000,
        output_sample_rate=44100
    )

    # lets write as multistream opus (supports only 48000 khz)
    stempeg.write_streams(
        "test.stem.opus",
        stems,
        sample_rate=96000,
        output_sample_rate=48000,
        codec="opus"
    )

    # writing to wav requires to convert streams to multichannel
    stempeg.write_streams(
        "test.wav",
        stems,
        sample_rate=96000,
        streams_as_multichannel=True
    )

    # TODO
    # stempeg also supports to load merged-multichannel streams using
    stems, rate = stempeg.read_streams(
        "test.wav",
        stems_from_multichannel=True
    )

    # mp3 does not support multiple channels,
    # therefore we have to use `streams_as_files`
    stempeg.write_streams(
        "out/test.mp3",
        stems,
        sample_rate=96000,
        output_sample_rate=44100,
        streams_as_files=True
    )
