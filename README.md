# stempeg = stems + ffmpeg
[![Build Status](https://travis-ci.org/faroit/stempeg.svg?branch=master)](https://travis-ci.org/faroit/stempeg)
[![Latest Version](https://img.shields.io/pypi/v/stempeg.svg)](https://pypi.python.org/pypi/stempeg)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/stempeg.svg)](https://pypi.python.org/pypi/stempeg)

python tool to read and write [STEM](https://www.native-instruments.com/en/specials/stems/) files.
Technically it is just wrapper for [ffmpeg](https://www.ffmpeg.org/) that makes it easier to handle multistream MP4 audio files.

## Installation

### 1. Installation of FFMPEG Library

_stempeg_ relies on [ffmpeg](https://www.ffmpeg.org/) to encode and decode the stems file format.

The Installation if ffmpeg differ among operating systems. If you use [Anaconda](https://anaconda.org/anaconda/python) you can install ffmpeg on Windows/Mac/Linux using the following command:

```
conda install -c conda-forge ffmpeg
```

__Decoding__ is supported with any recent build of ffmpeg. For __Encoding__ it is recommended to use the Fraunhofer AAC encoder (`libfdk_aac`) which is not included in the default ffmpeg builds. Note that the conda version currently does _not_ include `fdk-aac`. If `libfdk_aac` is not installed _stempeg_ will use the default `aac` codec which will result in slightly inferior audio quality.

You can install ffmpeg with `libfdk-aac` support manually as following:

* Mac: use homebrew: `brew install ffmpeg --with-fdk-aac`
* Ubuntu Linux: See installation script [here](https://gist.github.com/rafaelbiriba/7f2d7c6f6c3d6ae2a5cb).
* Using Docker (Mac, Windows, Linux): `docker pull jrottenberg/ffmpeg`

### 2. Installation of the _stempeg_ package

Installation via PyPI using pip

```
pip install stempeg
```

## Usage

There are very few freely available stem files. We [included](https://raw.githubusercontent.com/faroit/stempeg/master/tests/data/The%20Easton%20Ellises%20-%20Falcon%2069.stem.mp4) a small test track from the Canadian rock-band _The Easton Ellises_. The band [released them](https://www.heise.de/ct/artikel/c-t-Remix-Wettbewerb-The-Easton-Ellises-2542427.html) under Creative Commons license CC BY-NC-SA 3.0.

### Reading stems

```python
import stempeg
S, rate = stempeg.read_stems("input.stem.mp4")
```

`S` is the stem tensor that includes the time domain signals scaled to `[-1..1]`. The shape is `(stems, samples, channels)`.

### Reading individual stem ids

you can read individual substreams of the stem file by passing the corresponding stem id (starting from 0):

```python
S, rate = stempeg.read_stems("input.stem.mp4", stem_id=[0, 1])
```

### Writing stems

> :warning: __Warning__: Muxing stems using ffmpeg might lead to non conform stems. Please use MP4Box, if you need a reliable result.

Writing stem files from a numpy tensor

```python
stempeg.write_stems(S, "output.stem.mp4", rate=44100)
```

### Use the command line tools

#### Convert a stem to wav files


```bash
stem2wav tests/data/The Easton Ellises - Falcon 69.stem.mp4
```
