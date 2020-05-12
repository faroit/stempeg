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

# save stems from tensor as multi-stream mp4
stempeg.write_stems(
    "test.stem.mp4",
    stems,
    sample_rate=96000
)

# save stems from dict as multi-stream mp4
stempeg.write_stems(
    "test.stem.mp4",
    data={
        "mix": stems[0],
        "drums": stems[1],
        "bass": stems[2],
        "other": stems[3],
        "vocals": stems[4],
    },
    sample_rate=96000
)

# `write_stems` is a preset for the following settings
# here the output signal is resampled to 44100 Hz and AAC codec is used
stempeg.write_stems(
    "test.stem.mp4",
    stems,
    codec="aac",
    bitrate="256000",
    sample_rate=96000,
    output_sample_rate=44100
)

# lets write as multistream opus (supports only 48000 khz)
stempeg.write_stems(
    "test.stem.opus",
    stems,
    sample_rate=96000,
    output_sample_rate=48000,
    codec="opus"
)

# writing to wav requires to convert streams to multichannel
stempeg.write_stems(
    "test.wav",
    stems,
    sample_rate=96000,
    stems_as_channels=True
)

# stempeg also supports to load merged-multichannel streams using
stems, rate = stempeg.read_stems(
    "test.wav",
    stems_from_channels=2
)

# mp3 does not support multiple channels,
# therefore we have to use `stems_as_files`
# outputs are named ["output/0.mp3", "output/1.mp3"]
# for named files, provide a dict or use `stream_names`
stempeg.write_stems(
    "test.stem/*.ogg",
    stems,
    sample_rate=96000,
    output_sample_rate=44100,
    stems_as_files=True,
    stream_names=["mix", "drums", "bass", "other", "vocals"]
)
