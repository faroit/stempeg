import numpy as np
import subprocess as sp
import os
import json
import warnings
import tempfile as tmp
import soundfile as sf

DEVNULL = open(os.devnull, 'w')

class Info(object):
    """Abstract Info that holds the return of ffprobe
    
    """

    def __init__(self, filename):
        super(Info, self).__init__()
        self.filename = filename
        self.json_info = read_info(self.filename)

    @property
    def nb_audio_streams(self):
        return sum(
            [s['codec_type'] == 'audio' for s in self.json_info['streams']]
        )

    @property
    def nb_samples_streams(self):
        return [self.samples(k) for k, stream in enumerate(self.json_info['streams'])]

    @property
    def duration_streams(self):
        return [self.duration(k) for k, stream in enumerate(self.json_info['streams'])]

    def audio_stream_idx(self):
        return [
            s['index']
            for s in self.json_info['streams']
            if s['codec_type'] == 'audio'
        ]

    def samples(self, stream):
        return int(self.json_info['streams'][stream]['duration_ts'])

    def duration(self, stream):
        return float(self.json_info['streams'][stream]['duration'])
    
    def rate(self, stream):
        return int(self.json_info['streams'][stream]['sample_rate'])

    def channels(self, stream):
        return int(self.json_info['streams'][stream]['channels'])


def read_info(
    filename
):
    """Extracts FFMPEG info and returns info as JSON

    Returns
    -------
    info : Dict
        JSON info dict
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
    stem_id=None,
    start=0,
    duration=None,
    info=None
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
    start : float
        Start position (seek) in seconds, defaults to 0.
    duration : float
        Read `duration` seconds. End position then is `start + duration`.
        Defaults to `None`: read till the end.
    info : object
        provide info object, useful if read_stems is called frequently on
        file with same configuration (#streams, #channels, samplerate).
    Returns
    -------
    stems : array_like
        The tensor of Matrix of stems. The data shape is formatted as
        :code:`stems x channels x samples`.

    Notes
    -----

    Input is expected to be in 16bit/44.1 kHz

    """
    if info is None:
        FFinfo = Info(filename)
    else:
        FFinfo = info

    if stem_id is not None:
        substreams = stem_id
    else:
        substreams = FFinfo.audio_stream_idx()

    if not isinstance(substreams, list):
        substreams = [substreams]

    tmps = tmp.NamedTemporaryFile(delete=False, suffix='.wav')
    rate = FFinfo.rate(0)
    channels = FFinfo.channels(0)
    cmd = [
        'ffmpeg',
        '-y',
        '-vn',
        '-i', filename,
        '-filter_complex', "[0:0][0:1][0:2][0:3][0:4] amerge=inputs=5",
        '-acodec', 'pcm_s16le',
        '-ar', str(rate),
        '-ac', str(channels * len(substreams)),
        '-loglevel', 'error',
        tmps.name
    ]
    if start:
        cmd.insert(3, '-ss')
        cmd.insert(4, str(start))

    if duration is not None:
        cmd.insert(-1, '-t')
        cmd.insert(-1, str(duration))

    sp.call(cmd)
    print(cmd)
    # read wav files
    audio, rate = sf.read(tmps.name)
    tmps.close()
    os.remove(tmps.name)

    # # check if all stems have the same duration
    # stem_durations = np.array([t.shape[0] for t in stems])
    # if not (stem_durations == stem_durations[0]).all():
    #     warnings.warn("Warning.......Stems differ in length and were shortend")
    #     min_length = np.min(stem_durations)
    #     stems = [t[:min_length, :] for t in stems]

    stems = []
    for tmp_id, stem in enumerate(substreams):
        stems.append(audio[..., tmp_id*2:(tmp_id*2)+2])
    stems = np.array(stems)
    stems = np.squeeze(stems).astype(out_type)
    return stems, rate
