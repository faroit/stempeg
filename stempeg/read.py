from stempeg.write import FilesWriter
import numpy as np
import warnings
import ffmpeg
import pprint
from multiprocessing import Pool
import atexit
from functools import partial
import datetime as dt

class Reader(object):
    """Base class for reader

    Holds reader options
    """

    def __init__(self):
        pass


class StreamsReader(Reader):
    """Holding configuration for streams

    This is the default reader. Nothing to be hold
    """

    def __init__(self):
        pass


class ChannelsReader(Reader):
    """Using multichannels to multiplex to stems

    stems will be extracted from multichannel-pairs
    e.g. 8 channels will be converted to 4 stereo pairs


    Args:
        from_channels: int
            number of channels, defaults to `2`.
    """

    def __init__(self, nb_channels=2):
        self.nb_channels = nb_channels


def _read_ffmpeg(
    filename,
    sample_rate,
    metadata,
    start,
    duration,
    dtype,
    stem_idx
):
    channels = metadata.channels(stem_idx)
    output_kwargs = {'format': 'f32le', 'ar': sample_rate}
    if duration is not None:
        output_kwargs['t'] = str(dt.timedelta(seconds=duration))
    if start is not None:
        output_kwargs['ss'] = str(dt.timedelta(seconds=start))

    output_kwargs['map'] = '0:' + str(stem_idx)
    process = (
        ffmpeg
        .input(filename)
        .output('pipe:', **output_kwargs)
        .run_async(pipe_stdout=True, pipe_stderr=True))
    buffer, _ = process.communicate()
    waveform = np.frombuffer(buffer, dtype='<f4').reshape(-1, channels)
    if not waveform.dtype == np.dtype(dtype):
        waveform = waveform.astype(dtype)
    return waveform


def read_stems(
    filename,
    start=None,
    duration=None,
    stem_id=None,
    always_3d=False,
    dtype=np.float32,
    info=None,
    sample_rate=None,
    reader=StreamsReader(),
    multiprocess=False
):
    """Read stems into numpy tensor

    Args:
        filename: str, required
            filename of the audio file to load data from.
        start: float, optional
            Start offset to load from in seconds.
        duration: float, optional
            Duration to load in seconds.
        stem_id: int, optional
            subbstream id, defauls to `None` (all substreams are loaded)
        always_3d: bool, optional
            By default, reading a single-stream audio file will return a
            two-dimensional array.  With ``always_3d=True``, audio data is
            always returned as a three-dimensional array, even if the audio
            file has only one stream.
        dtype: np.dtype, optional
            Numpy data type to use, default to `np.float32`.
        info: Info, Optional
            Pass ffmpeg `Info` object to reduce number of os calls on file.
        sample_rate: float, optional
            Sample rate of returned audio. Defaults to `None` which results in
            the sample rate returned from the mixture.
        reader: Reader
            Holds parameters for the actual reading method
            Currently this can be one of the following:
                `StreamsReader(...)`
                    Read from a single multistream audio (default)
                `ChannelsReader(...)`
                    Read/demultiplexed from multiple channels
        multiprocess: bool
            Applys multiprocessing for reading substreams.
            Defaults to `False`

    Returns:
        stems: array_like
            stems tensor of `shape=(stem x samples x channels)`
        rate: float
            sample rate
    """
    if multiprocess:
        _pool = Pool()
        atexit.register(_pool.close)
    else:
        _pool = None

    if not isinstance(filename, str):
        filename = filename.decode()

    # use ffprobe to get info object (samplerate, lengths)
    try:
        if info is None:
            metadata = Info(filename)
        else:
            metadata = info

        ffmpeg.probe(filename)
    except ffmpeg._run.Error as e:
        raise Warning(
            'An error occurs with ffprobe (see ffprobe output below)\n\n{}'
            .format(e.stderr.decode()))

    # check number of audio streams in file
    if 'streams' not in metadata.info or metadata.nb_audio_streams == 0:
        raise Warning('No audio stream found.')

    # using ChannelReader would ignore substreams
    if isinstance(reader, ChannelsReader):
        if metadata.nb_audio_streams != 1:
            raise Warning(
                'stempeg.ChannelsReader() only processes the first substream.'
            )
        else:
            if metadata.audio_streams[0][
                'channels'
            ] % reader.nb_channels != 0:
                raise Warning('Stems should be encoded as multi-channel.')
            else:
                substreams = 0
    else:
        if stem_id is not None:
            substreams = stem_id
        else:
            substreams = metadata.audio_stream_idx()

    if not isinstance(substreams, list):
        substreams = [substreams]

    # if not, get sample rate from mixture
    if sample_rate is None:
        sample_rate = metadata.sample_rate(0)

    stems = []

    if _pool:
        results = _pool.map_async(
            partial(
                _read_ffmpeg,
                filename,
                sample_rate,
                metadata,
                start,
                duration,
                dtype
            ),
            substreams,
            callback=stems.extend
        )
        results.wait()
        _pool.terminate()
    else:
        stems = [
            _read_ffmpeg(
                filename,
                sample_rate,
                metadata,
                start,
                duration,
                dtype,
                stem_idx
            )
            for stem_idx in substreams
        ]
    stem_durations = np.array([t.shape[0] for t in stems])
    if not (stem_durations == stem_durations[0]).all():
        warnings.warning("Stems differ in length and were shortend")
        min_length = np.min(stem_durations)
        stems = [t[:min_length, :] for t in stems]

    # aggregate list of stems to numpy tensor
    stems = np.array(stems)

    # If ChannelsReader is used, demultiplex from channels
    if isinstance(reader, (ChannelsReader)) and stems.shape[-1] > 1:
        stems = stems.transpose(1, 0, 2)
        stems = stems.reshape(
            stems.shape[0], stems.shape[1], -1, reader.nb_channels
        )
        stems = stems.transpose(2, 0, 3, 1)[..., 0]

    if not always_3d:
        stems = np.squeeze(stems)
    return stems, sample_rate


class Info(object):
    """Abstract Info that holds the return of ffprobe"""

    def __init__(self, filename):
        super(Info, self).__init__()
        self.info = ffmpeg.probe(filename)
        self.audio_streams = [
            stream for stream in self.info['streams']
            if stream['codec_type'] == 'audio'
        ]

    @property
    def nb_audio_streams(self):
        """Returns the number of audio substreams"""
        return len(self.audio_streams)

    @property
    def nb_samples_streams(self):
        """Returns a list of number of samples for each substream"""
        return [self.samples(k) for k, stream in enumerate(self.audio_streams)]

    @property
    def duration_streams(self):
        """Returns a list of durations (in s) for all substreams"""
        return [
            self.duration(k) for k, stream in enumerate(self.audio_streams)
        ]

    @property
    def title_streams(self):
        """Returns stream titles for all substreams"""
        return [
            stream['tags'].get('handler_name')
            for stream in self.audio_streams
        ]

    def audio_stream_idx(self):
        """Returns audio substream indices"""
        return [s['index'] for s in self.audio_streams]

    def samples(self, idx):
        """Returns the number of samples for a stream index"""
        return int(self.audio_streams[idx]['duration_ts'])

    def duration(self, idx):
        """Returns the duration (in seconds) for a stream index"""
        return float(self.audio_streams[idx]['duration'])

    def title(self, idx):
        """Return the `handler_name` metadata for a given stream index"""
        return self.audio_streams[idx]['tags']['handler_name']

    def rate(self, idx):
        # deprecated from older stempeg version
        return self.sample_rate(idx)

    def sample_rate(self, idx):
        """Return sample rate for a given substream"""
        return int(self.audio_streams[idx]['sample_rate'])

    def channels(self, idx):
        """Returns the number of channels for a gvien substream"""
        return int(self.audio_streams[idx]['channels'])

    def __repr__(self):
        """Print stream information"""
        return pprint.pformat(self.audio_streams)
