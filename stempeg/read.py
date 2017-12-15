import numpy as np
import subprocess as sp
import os
import json
import warnings

DEVNULL = open(os.devnull, 'w')


class FFMPEGInfo(object):
    """docstring for FFMPEGInfo."""
    def __init__(self, filename):
        super(FFMPEGInfo, self).__init__()
        self.filename = filename
        self.json_info = read_info(self.filename)

    @property
    def nb_audio_streams(self):
        return sum(
            [s['codec_type'] == 'audio' for s in self.json_info['streams']]
        )

    def audio_stream_idx(self):
        return [
            s['index']
            for s in self.json_info['streams']
            if s['codec_type'] == 'audio'
        ]

    def rate(self, stream):
        return int(self.json_info['streams'][stream]['sample_rate'])

    def channels(self, stream):
        return int(self.json_info['streams'][stream]['channels'])


def read_info(
    filename
):
    cmd = [
        'ffprobe',
        filename,
        '-v', 'quiet',
        '-print_format', 'json',
        '-show_format', '-show_streams',
    ]

    out = sp.check_output(cmd)
    info = json.loads(out.decode('utf-8'))
    return info


def read_stems(
    filename,
    out_type=np.float_,
    stem_idx=None
):
    """Read STEMS format into numpy Tensor

    Parameters
    ----------
    filename : str
        Filename of STEMS format. Typically `filename.stem.mp4`.
    out_type : type
        Output type. Defaults to 32bit float aka `np.float32`.
    stem_idx : int
        Stem ID (Stream ID) to read. Defaults to `None`, which reads all
        available stems.


    Returns
    -------
    stems : array_like
        The tensor of Matrix of stems. The date shape is formatted as
        :code:`stems x samples x channels`.

    Notes
    -----

    Input is expected to be in 16bit/44.1 kHz

    """

    FFinfo = FFMPEGInfo(filename)

    stems = []

    if stem_idx is not None:
        substreams = stem_idx
    else:
        substreams = FFinfo.audio_stream_idx()

    for substream in substreams:
        sr = FFinfo.rate(substream)
        channels = FFinfo.channels(substream)
        cmd = [
            'ffmpeg',
            '-i', filename,
            '-f', 's16le',
            '-map', '0:' + str(substream),
            '-acodec', 'pcm_s16le',
            '-ar', str(sr),
            '-ac', str(channels),
            '-'
        ]
        p = sp.Popen(cmd, stdout=sp.PIPE, stderr=DEVNULL, bufsize=4096)
        bytes_per_sample = np.dtype(np.int16).itemsize
        frame_size = bytes_per_sample * channels
        chunk_size = frame_size * sr  # read in 1-second chunks
        raw = b''
        with p.stdout as stdout:
            while True:
                data = stdout.read(chunk_size)
                if data:
                    raw += data
                else:
                    break
        audio = np.fromstring(raw, dtype=np.int16).astype(out_type)

        if channels > 1:
            audio = audio.reshape((-1, channels)).transpose()
        if audio.size == 0:
            return audio, sr
        if issubclass(out_type, np.floating):
            if issubclass(np.int16, np.integer):
                audio /= np.iinfo(np.int16).max

        stems.append(audio)

    # check if all stems have the same duration
    stem_durations = np.array([t.shape[1] for t in stems])
    if (stem_durations == stem_durations[0]).all():
        warnings.warn("Warning.......Stems differ in length and were shortend")
        min_length = np.min(stem_durations)
        stems = [t[:, :min_length] for t in stems]

    stems = np.swapaxes(np.array(stems), 1, 2)
    return stems, sr
