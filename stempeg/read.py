import numpy as np
import os.path
import subprocess
import subprocess as sp
import os
import json
import warnings
import ffmpeg
import pprint


def _to_ffmpeg_time(n):
    """ Format number of seconds to time expected by FFMPEG.
    :param n: Time in seconds to format.
    :returns: Formatted time in FFMPEG format.
    """
    m, s = divmod(n, 60)
    h, m = divmod(m, 60)
    return '%d:%02d:%09.6f' % (h, m, s)


def read_stems(
    filename,
    start=None,
    duration=None,
    stem_id=None,
    dtype=np.float32,
    info=None,
    stems_from_multichannel=False
):
    """ Loads the audio file denoted by the given path
    and returns it data as a waveform.
    :param filename: filename of the audio file to load data from.
    :param offset: (Optional) Start offset to load from in seconds.
    :param duration: (Optional) Duration to load in seconds.
    :param sample_rate: (Optional) Sample rate to load audio with.
    :param dtype: (Optional) Numpy data type to use, default to float32.
    :returns: Loaded data a (waveform, sample_rate) tuple.
    :raise SpleeterError: If any error occurs while loading audio.
    """
    if not isinstance(filename, str):
        filename = filename.decode()
    try:
        if info is None:
            metadata = Info(filename)
        else:
            metadata = info

    except ffmpeg._run.Error as e:
        raise Warning(
            'An error occurs with ffprobe (see ffprobe output below)\n\n{}'
            .format(e.stderr.decode()))
    if 'streams' not in metadata.info or metadata.nb_audio_streams == 0:
        raise Warning('No stream was found with ffprobe')

    if stems_from_multichannel:
        if metadata.nb_audio_streams != 1:
            raise Warning('Stems should be encoded as 1 substream')
        else:
            if metadata.audio_streams[0]['channels'] % 2 != 0:
                raise Warning('Stems should be encoded as stereo pairs')
            else:
                substreams = 0
    else:
        substreams = metadata.audio_stream_idx()

    if not isinstance(substreams, list):
        substreams = [substreams]

    stems = []
    # apply some hack that fixes ffmpegs wrong read shape when using `-ss <0.000001`
    if start:
        if start < 1e-4:
            start = None

    for stem in substreams:
        rate = metadata.rate(stem)
        channels = metadata.channels(stem)
        output_kwargs = {'format': 'f32le', 'ar': rate}
        if duration is not None:
            output_kwargs['t'] = _to_ffmpeg_time(duration)
        if start is not None:
            output_kwargs['ss'] = _to_ffmpeg_time(start)

        output_kwargs['map'] = '0:' + str(stem)
        process = (
            ffmpeg
            .input(filename)
            .output('pipe:', **output_kwargs)
            .run_async(pipe_stdout=True, pipe_stderr=True))
        buffer, _ = process.communicate()
        waveform = np.frombuffer(buffer, dtype='<f4').reshape(-1, channels)
        if not waveform.dtype == np.dtype(dtype):
            waveform = waveform.astype(dtype)
        stems.append(waveform)

    stem_durations = np.array([t.shape[0] for t in stems])
    if not (stem_durations == stem_durations[0]).all():
        warnings.warn("Warning.......Stems differ in length and were shortend")
        min_length = np.min(stem_durations)
        stems = [t[:min_length, :] for t in stems]

    stems = np.array(stems)
    if stems_from_multichannel:
        stems = stems.reshape(
            stems.shape[0], stems.shape[1], 2, -1
        ).transpose(0, 3, 1, 2)

    stems = np.squeeze(stems)
    return stems, rate


class Info(object):
    """Abstract Info that holds the return of ffprobe"""

    def __init__(self, filename):
        super(Info, self).__init__()
        self.filename = filename
        self.info = ffmpeg.probe(filename)
        self.audio_streams = [
            stream for stream in self.info['streams']
            if stream['codec_type'] == 'audio'
        ]

    @property
    def nb_audio_streams(self):
        return len(self.audio_streams)

    @property
    def nb_samples_streams(self):
        return [self.samples(k) for k, stream in enumerate(self.audio_streams)]

    @property
    def duration_streams(self):
        return [
            self.duration(k) for k, stream in enumerate(self.audio_streams)
        ]

    def audio_stream_idx(self):
        return [s['index'] for s in self.audio_streams]

    def samples(self, idx):
        return int(self.audio_streams[idx]['duration_ts'])

    def duration(self, idx):
        return float(self.audio_streams[idx]['duration'])

    def rate(self, idx):
        return int(self.audio_streams[idx]['sample_rate'])

    def channels(self, idx):
        return int(self.audio_streams[idx]['channels'])

    def __repr__(self):
        return pprint.pformat(self.audio_streams)