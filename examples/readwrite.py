"""Opens a stem file and saves (re-encodes) back to a stem file
"""
import argparse
import stempeg
import subprocess as sp
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

    # load stems,
    # resample to 96000 Hz,
    # use multiprocessing
    stems, rate = stempeg.read_stems(
        args.input,
        sample_rate=96000,
        multiprocess=True
    )

    # --> stems now has `shape=(stem x samples x channels)``

    # save stems from tensor as multi-stream mp4
    stempeg.write_stems(
        "test.stem.m4a",
        stems,
        sample_rate=96000
    )

    # save stems as dict for convenience
    stems = {
        "mix": stems[0],
        "drums": stems[1],
        "bass": stems[2],
        "other": stems[3],
        "vocals": stems[4],
    }
    # keys will be automatically used

    # from dict as files
    stempeg.write_stems(
        "test.stem.m4a",
        data=stems,
        sample_rate=96000
    )

    # `write_stems` is a preset for the following settings
    # here the output signal is resampled to 44100 Hz and AAC codec is used
    stempeg.write_stems(
        "test.stem.m4a",
        stems,
        sample_rate=96000,
        writer=stempeg.StreamsWriter(
            codec="aac",
            output_sample_rate=44100,
            bitrate="256000",
            stem_names=['mix', 'drums', 'bass', 'other', 'vocals']
        )
    )

    # Native Instruments compatible stems
    stempeg.write_stems(
        "test_traktor.stem.m4a",
        stems,
        sample_rate=96000,
        writer=stempeg.NIStemsWriter(
            stems_metadata=[
                {"color": "#009E73", "name": "Drums"},
                {"color": "#D55E00", "name": "Bass"},
                {"color": "#CC79A7", "name": "Other"},
                {"color": "#56B4E9", "name": "Vocals"}
            ]
        )
    )

    # lets write as multistream opus (supports only 48000 khz)
    stempeg.write_stems(
        "test.stem.opus",
        stems,
        sample_rate=96000,
        writer=stempeg.StreamsWriter(
            output_sample_rate=48000,
            codec="opus"
        )
    )

    # writing to wav requires to convert streams to multichannel
    stempeg.write_stems(
        "test.wav",
        stems,
        sample_rate=96000,
        writer=stempeg.ChannelsWriter(
            output_sample_rate=48000
        )
    )

    # # stempeg also supports to load merged-multichannel streams using
    stems, rate = stempeg.read_stems(
        "test.wav",
        reader=stempeg.ChannelsReader(nb_channels=2)
    )

    # mp3 does not support multiple channels,
    # therefore we have to use `stempeg.FilesWriter`
    # outputs are named ["output/0.mp3", "output/1.mp3"]
    # for named files, provide a dict or use `stem_names`
    # also apply multiprocessing
    stempeg.write_stems(
        ("output", ".mp3"),
        stems,
        sample_rate=rate,
        writer=stempeg.FilesWriter(
            multiprocess=True,
            output_sample_rate=48000,
            stem_names=["mix", "drums", "bass", "other", "vocals"]
        )
    )
