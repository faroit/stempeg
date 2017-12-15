# stempeg (STEMS + FFMPEG)

python tool to read and write [STEM](https://www.native-instruments.com/en/specials/stems/) files.
Technically it is just wrapper

## Installation

### FFMPEG Library

stempeg uses ffmpeg to encode and decode the stems file format. Installation
if ffmpeg differ among operating systems

* Mac: use homebrew: `brew install ffmpeg --with-fdk-aac`

### pip

Installation via PyPI using pip

```
pip install stempeg
```

## Usage

### Reading stems

```python
import stempeg
S, sr = stempeg.read_stems(args.input)
```

`S` is the stems tensor. The shape is formatted as `stems x samples x channels`

### Writing stems

__Warning__: Muxing stems using ffmpeg might lead in non conform stem. Please use MP4Box, if you need a realiable result.


Writing stem files from a numpy tensor

```python
stempeg.write_stems(S, "out.stem.mp4", sr=44100)
```
