import os

import ffmpeg
import numpy as np
import soundfile as sf


test_vectors = {
    "MP3": "https://samples.ffmpeg.org/A-codecs/MP3/Enrique.mp3",
    "AAC": "https://samples.ffmpeg.org/A-codecs/AAC/ct_nero-heaac.mp4",
    "OGG": "https://samples.ffmpeg.org/A-codecs/vorbis/ffvorbis_crash.ogm",
    "WAV": "https://samples.ffmpeg.org/A-codecs/wavpcm/madbear.wav"
}


def load_audio_ffmpeg(path, dtype=np.float32, n_channels=2):
    """
        load audio file from ffmpeg
    """
    if dtype == np.float32:
        ffmpeg_format = "f32le"
        numpy_dtype = '<f4'
    elif dtype == np.int16:
        ffmpeg_format = "s16le"
        numpy_dtype = '<i2'
    else:
        raise ValueError(f"Unknown dtype: {dtype}")

    output_kwargs = {'format': ffmpeg_format}
    process = (
        ffmpeg.input(path).output('pipe:', **output_kwargs).run_async(pipe_stdout=True, pipe_stderr=True))

    buffer, _ = process.communicate()
    waveform = np.frombuffer(buffer, dtype=numpy_dtype).reshape(-1, n_channels)
    return waveform


def s16_to_f32(waveform_s16):
    """ convert int16 waveform to normalized float32 waveform """
    return waveform_s16.astype(np.float32) / 32768.0


for container, url in test_vectors.items():
    waveform_s16 = load_audio_ffmpeg(url, dtype=np.int16)
    waveform_f32 = load_audio_ffmpeg(url, dtype=np.float32)

    print(container)
    print("Average absolute error between ffmpeg int16 and float32 loading:")
    print(np.abs(s16_to_f32(waveform_s16) - waveform_f32).mean())
