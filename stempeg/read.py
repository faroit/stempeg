import numpy as np
import subprocess as sp
import os
DEVNULL = open(os.devnull, 'w')


def read_stems(
    filename,
    mono=False,
    out_type=np.float
):
    """Read STEMS format into numpy Tensor

    Parameters
    ----------
    filename : str
        Filename of STEMS format. Typically `filename.stem.mp4`
    centered : boolean
        STEMS format is stereo only. Setting :code:`mono=True` downmixes to the
        output to mono. Also reduces the dimensions to 2. Defaults to False.
    out_type : type
        Output type. Defaults to 32bit float aka `np.float32`.

    Returns
    -------
    stems : array_like
        The tensor of Matrix of stems. The date shape is formatted as
        :code:`stems x channels x samples`. In case of a `mono=True`,
        the shape is :code:`stems x samples`.

    Notes
    -----
    ...
    """

    sr = 44100
    channels = 1 if mono else 2
    stems = []
    for substream in range(5):
        command = [
            'ffmpeg',
            '-i', filename,
            '-f', 's16le',
            '-map', '0:' + str(substream),
            '-acodec', 'pcm_s16le',
            '-ar', str(sr),
            '-ac', str(channels),
            '-']
        p = sp.Popen(command, stdout=sp.PIPE, stderr=DEVNULL, bufsize=4096)
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

    return np.array(stems), sr
