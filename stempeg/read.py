import numpy as np
import subprocess as sp
import os
import json
import warnings
import tempfile as tmp
import soundfile as sf

DEVNULL = open(os.devnull, 'w')


class FFMPEGInfo(object):
    """Abstract FFMPEGInfo Object
    """

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
    """Extracts FFMPEG info and returns info as json
    """

    cmd = [
        'ffprobe',
        filename,
        '-v', 'error',
        '-print_format', 'json',
        '-show_format', '-show_streams',
    ]

    out = sp.check_output(cmd)
    info = json.loads(out.decode('utf-8'))
    return info


def read_stems(
    filename,
    out_type=np.float_,
    stem_id=None
):
    """Read STEMS format into numpy Tensor

    Parameters
    ----------
    filename : str
        Filename of STEMS format. Typically `filename.stem.mp4`.
    out_type : type
        Output type. Defaults to 32bit float aka `np.float32`.
    stem_id : int
        Stem ID (Stream ID) to read. Defaults to `None`, which reads all
        available stems.


    Returns
    -------
    stems : array_like
        The tensor of Matrix of stems. The data shape is formatted as
        :code:`stems x channels x samples`.

    Notes
    -----

    Input is expected to be in 16bit/44.1 kHz

    """

    FFinfo = FFMPEGInfo(filename)

    if stem_id is not None:
        substreams = stem_id
    else:
        substreams = FFinfo.audio_stream_idx()

    if not isinstance(substreams, list):
        substreams = [substreams]

    stems = []
    tmps = [
        tmp.NamedTemporaryFile(delete=False, suffix='.wav')
        for t in substreams
    ]
    for tmp_id, stem in enumerate(substreams):
        rate = FFinfo.rate(stem)
        channels = FFinfo.channels(stem)
        cmd = [
            'ffmpeg',
            '-y',
            '-vn',
            '-i', filename,
            '-map', '0:' + str(stem),
            '-acodec', 'pcm_s16le',
            '-ar', str(rate),
            '-ac', str(channels),
            '-loglevel', 'error',
            tmps[tmp_id].name
        ]
        sp.call(cmd)
        # read wav files
        audio, rate = sf.read(tmps[tmp_id].name)
        tmps[tmp_id].close()
        os.remove(tmps[tmp_id].name)
        stems.append(audio)

    # check if all stems have the same duration
    stem_durations = np.array([t.shape[0] for t in stems])
    if not (stem_durations == stem_durations[0]).all():
        warnings.warn("Warning.......Stems differ in length and were shortend")
        min_length = np.min(stem_durations)
        stems = [t[:min_length, :] for t in stems]

    stems = np.array(stems)
    stems = np.squeeze(stems)
    return stems, rate
