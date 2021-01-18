import numpy as np

# run ffmpeg command
# -ar is your target sample rate to which ffmpeg will resample it to
# ffmpeg -i input.mp3 -f f32le -acodec pcm_f32le -ar 44100 out.raw

filePath = "out.raw"
file = open(filePath, "rb")
with file:
    bytes = file.read()

waveform = np.frombuffer(bytes, dtype='<f4').reshape(-1, 2)
print(waveform.shape)