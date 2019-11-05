import numpy as np  # pylint: disable=import-error
import re
import platform
import os.path
from os.path import exists
from importlib import import_module
from abc import ABC, abstractmethod
import subprocess
import numpy as np
import subprocess as sp
import os
import json
import warnings
import tempfile as tmp
import decimal
import soundfile as sf
import os
# Default FFMPEG binary name.
_UNIX_BINARY = 'ffmpeg'
_WINDOWS_BINARY = 'ffmpeg.exe'

def _which(program):
    """ A pure python implementation of `which`command
    for retrieving absolute path from command name or path.
    @see https://stackoverflow.com/a/377028/1211342
    :param program: Program name or path to expend.
    :returns: Absolute path of program if any, None otherwise.
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, _ = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ['PATH'].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def _get_ffmpeg_path():
    """ Retrieves FFMPEG binary path using ENVVAR if defined
    or default binary name (Windows or UNIX style).
    :returns: Absolute path of FFMPEG binary.
    :raise IOError: If FFMPEG binary cannot be found.
    """
    ffmpeg_path = os.environ.get('FFMPEG_PATH', None)
    if ffmpeg_path is None:
        # Note: try to infer standard binary name regarding of platform.
        if platform.system() == 'Windows':
            ffmpeg_path = _WINDOWS_BINARY
        else:
            ffmpeg_path = _UNIX_BINARY
    expended = _which(ffmpeg_path)
    if expended is None:
        raise IOError(f'FFMPEG binary ({ffmpeg_path}) not found')
    return expended


def _to_ffmpeg_time(n):
    """ Format number of seconds to time expected by FFMPEG.
    :param n: Time in seconds to format.
    :returns: Formatted time in FFMPEG format.
    """
    m, s = divmod(n, 60)
    h, m = divmod(m, 60)
    return '%d:%02d:%09.6f' % (h, m, s)


def _parse_ffmpg_results(stderr):
    """ Extract number of channels and sample rate from
    the given FFMPEG STDERR output line.
    :param stderr: STDERR output line to parse.
    :returns: Parsed n_channels and sample_rate values.
    """
    # Setup default value.
    n_channels = 0
    sample_rate = 0
    # Find samplerate
    match = re.search(r'(\d+) hz', stderr)
    if match:
        sample_rate = int(match.group(1))
    # Channel count.
    match = re.search(r'hz, ([^,]+),', stderr)
    if match:
        mode = match.group(1)
        if mode == 'stereo':
            n_channels = 2
        else:
            match = re.match(r'(\d+) ', mode)
            n_channels = match and int(match.group(1)) or 1
    return n_channels, sample_rate


class _CommandBuilder(object):
    """ A simple builder pattern class for CLI string. """

    def __init__(self, binary):
        """ Default constructor. """
        self._command = [binary]

    def flag(self, flag):
        """ Add flag or unlabelled opt. """
        self._command.append(flag)
        return self

    def opt(self, short, value, formatter=str):
        """ Add option if value not None. """
        if value is not None:
            self._command.append(short)
            self._command.append(formatter(value))
        return self

    def command(self):
        """ Build string command. """
        return self._command


class FFMPEGProcessAudioAdapter(object):
    """ An AudioAdapter implementation that use FFMPEG binary through
    subprocess in order to perform I/O operation for audio processing.
    When created, FFMPEG binary path will be checked and expended,
    raising exception if not found. Such path could be infered using
    FFMPEG_PATH environment variable.
    """

    def __init__(self):
        """ Default constructor. """
        self._ffmpeg_path = _get_ffmpeg_path()

    def _get_command_builder(self):
        """ Creates and returns a command builder using FFMPEG path.
        :returns: Built command builder.
        """
        return _CommandBuilder(self._ffmpeg_path)

    def load(
            self, path, offset=None, duration=None, stem_id=None,
            sample_rate=None, dtype=np.float32):
        """ Loads the audio file denoted by the given path
        and returns it data as a waveform.
        :param path: Path of the audio file to load data from.
        :param offset: (Optional) Start offset to load from in seconds.
        :param duration: (Optional) Duration to load in seconds.
        :param sample_rate: (Optional) Sample rate to load audio with.
        :param dtype: (Optional) Numpy data type to use, default to float32.
        :returns: Loaded data a (waveform, sample_rate) tuple.
        """
        if not isinstance(path, str):
            path = path.decode()
        command = (
            self._get_command_builder()
            .opt('-ss', offset, formatter=float_to_str)
            .opt('-t', duration, formatter=float_to_str)
            .opt('-i', path)
            .opt('-ar', sample_rate)
            .opt('-map', '0:' + str(0))
            .opt('-f', 'f32le')
            .flag('-')
            .command())
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        buffer = process.stdout.read(-1)
        # Read STDERR until end of the process detected.
        while True:
            status = process.stderr.readline()
            if not status:
                raise OSError('Stream info not found')
            if isinstance(status, bytes):  # Note: Python 3 compatibility.
                status = status.decode('utf8', 'ignore')
            status = status.strip().lower()
            if 'no such file' in status:
                raise IOError(f'File {path} not found')
            elif 'invalid data found' in status:
                raise IOError(f'FFMPEG error : {status}')
            elif 'audio:' in status:
                n_channels, ffmpeg_sample_rate = _parse_ffmpg_results(status)
                if sample_rate is None:
                    sample_rate = ffmpeg_sample_rate
                break
        # Load waveform and clean process.
        waveform = np.frombuffer(buffer, dtype='<f4').reshape(-1, n_channels)
        if not waveform.dtype == np.dtype(dtype):
            waveform = waveform.astype(dtype)
        process.stdout.close()
        process.stderr.close()
        del process
        return (waveform, sample_rate)


def float_to_str(f, precision=5):
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    # create a new context for this task
    ctx = decimal.Context(rounding=decimal.ROUND_DOWN)

    # 12 digits should be enough to represent a single sample of
    # 192khz in float
    ctx.prec = precision

    d1 = ctx.create_decimal(repr(round(f, 5)))
    return format(d1, 'f')


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

    stems = []
    loader = FFMPEGProcessAudioAdapter()
    # apply some hack that fixes ffmpegs wrong read shape when using `-ss <0.000001`
    if start:
        if start < 1e-4:
            start = None

    for stream_id in substreams:
        audio, rate = loader.load(
            filename, offset=start, duration=duration, stem_id=stream_id
        )
        stems.append(audio)

    stem_durations = np.array([t.shape[0] for t in stems])
    if not (stem_durations == stem_durations[0]).all():
        warnings.warn("Warning.......Stems differ in length and were shortend")
        min_length = np.min(stem_durations)
        stems = [t[:min_length, :] for t in stems]

    stems = np.array(stems)
    stems = np.squeeze(stems).astype(out_type)
    return stems, rate
