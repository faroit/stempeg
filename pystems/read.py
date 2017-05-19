import numpy as np
import subprocess as sp
import os
DEVNULL = open(os.devnull, 'w')


def read_stems(
    filename,
    mono=False,
    out_type=np.float32
):
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
