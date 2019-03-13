# stempeg = stems + ffmpeg

[![Build Status](https://travis-ci.org/faroit/stempeg.svg?branch=master)](https://travis-ci.org/faroit/stempeg)
[![Latest Version](https://img.shields.io/pypi/v/stempeg.svg)](https://pypi.python.org/pypi/stempeg)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/stempeg.svg)](https://pypi.python.org/pypi/stempeg)

python package to read and write [STEM](https://www.native-instruments.com/en/specials/stems/) files.
Technically, STEMs are MP4 files with multiple audio streams and additional metatdata, hence _stempeg_ wrapper for [ffmpeg](https://www.ffmpeg.org/) that makes it easier to handle multi stream MP4 audio files.

## Installation

### 1. Installation of ffmpeg Library

_stempeg_ relies on [ffmpeg](https://www.ffmpeg.org/) (tested: 4.1, 4.0.2, 3.4 and 2.8.6) to decode the stems file format. For
encoding ffmpeg >= 3.2 is suggested.

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

There are very few freely available stem files. We included a small test track from the Canadian rock-band _The Easton Ellises_. The band [released them](https://www.heise.de/ct/artikel/c-t-Remix-Wettbewerb-The-Easton-Ellises-2542427.html) under Creative Commons license CC BY-NC-SA 3.0.

To use the included stem example you can use `stempeg.example_stem_path()`.

### Reading stems

```python
import stempeg
S, rate = stempeg.read_stems(stempeg.example_stem_path())
```

`S` is the stem tensor that includes the time domain signals scaled to `[-1..1]`. The shape is `(stems, samples, channels)`.

### Reading individual stem ids

you can read individual substreams of the stem file by passing the corresponding stem id (starting from 0):

```python
S, rate = stempeg.read_stems(stempeg.example_stem_path(), stem_id=[0, 1])
```

### Read excerpts (set seek position)

to read an excerpt from the stem instead of the full file, you can provide start (`start`) and duration (`duration`) in seconds to `read_stems`:

```python
S, _ = stempeg.read_stems(stempeg.example_stem_path(), start=1, duration=1.5)
# read from second 1.0 to second 2.5
```

### Improve performance

if `read_stems` is called repeatedly, it always does two system calls, one for getting the [file info](https://github.com/faroit/stempeg/blob/a56349d2a8297ccf5db13712fc16048029503b26/stempeg/read.py#L120) and one for the [actual reading](https://github.com/faroit/stempeg/blob/a56349d2a8297ccf5db13712fc16048029503b26/stempeg/read.py#L160).  To speed this up you could provide the `Info` object to `read_stems` if the number of streams, the number of channels and the samplerate is identical.

```python
file_path = stempeg.example_stem_path()
info = stempeg.Info(file_path)
S, _ = stempeg.read_stems(file_path, info=info)
```

### Writing stems

Writing stem files from a numpy tensor

```python
stempeg.write_stems(S, "output.stem.mp4", rate=44100)
```

> :warning: __Warning__: Muxing stems using _ffmpeg_ might lead to non-conform stem files. Please use MP4Box, if you need a reliable result.


### Use the command line tools

_stempeg_ provides a convenient cli tool to convert a stem to multiple wavfiles. The `-s` switch sets the start, the `-t` switch sets the duration.


```bash
stem2wav The Easton Ellises - Falcon 69.stem.mp4 -s 1.0 -t 2.5
```
