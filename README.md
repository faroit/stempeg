# stempeg = stems + ffmpeg

[![Build Status](https://travis-ci.org/faroit/stempeg.svg?branch=master)](https://travis-ci.org/faroit/stempeg)
[![Latest Version](https://img.shields.io/pypi/v/stempeg.svg)](https://pypi.python.org/pypi/stempeg)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/stempeg.svg)](https://pypi.python.org/pypi/stempeg)

Python package to read and write [STEM](https://www.native-instruments.com/en/specials/stems/) files.
Technically, stems are audio containers that combine multiple audio streams and metadata in a single audio file. This makes it ideal to playback multitrack audio, where users can select the audio sub-stream during playback (e.g. supported by VLC). 

Under the hood, _stempeg_ uses [ffmpeg](https://www.ffmpeg.org/) for reading and writing multistream audio, optionally [MP4Box](https://github.com/gpac/gpac) is used to create STEM files that are compatible with Native Instruments hardware and software.

## Installation

### 1. Installation of ffmpeg Library

_stempeg_ relies on [ffmpeg](https://www.ffmpeg.org/) (>= 3.2 is suggested).

The Installation if ffmpeg differ among operating systems. If you use [Anaconda](https://anaconda.org/anaconda/python) you can install ffmpeg on Windows/Mac/Linux using the following command:

```
conda install -c conda-forge ffmpeg
```

Note that for better quality encoding it is recommended to install ffmpeg with `libfdk-aac` codec support as following:

* _MacOS_: use homebrew: `brew install ffmpeg --with-fdk-aac`
* _Ubuntu/Debian Linux_: See installation script [here](https://gist.github.com/rafaelbiriba/7f2d7c6f6c3d6ae2a5cb).
* _Docker_: `docker pull jrottenberg/ffmpeg`

### 1a. (optional) Installation of MP4Box

If you plan to write stem files with full compatibility with Native Instruments Traktor DJ hardware and software, you need to install [MP4Box](https://github.com/gpac/gpac).

* _MacOS_: use homebrew: `brew install gpac`
* _Ubuntu/Debian Linux_: `apt-get install gpac`

Further installation instructions for all operating systems can be found [here](https://gpac.wp.imt.fr/downloads/).

### 2. Installation of the _stempeg_ package

A) Installation via PyPI using pip

```
pip install stempeg
```

B) Installation via conda

```
conda install -c conda-forge stempeg
```

## Usage

A small excerpt from a music track by [The Easton Ellises](https://www.heise.de/ct/artikel/c-t-Remix-Wettbewerb-The-Easton-Ellises-2542427.html#englisch), licensed under Creative Commons CC BY-NC-SA 3.0 is included and can be accessed using `stempeg.example_stem_path()`.

### Reading stems

```python
import stempeg
S, rate = stempeg.read_stems(stempeg.example_stem_path())
```

`S` is a numpy tensor that includes the time domain signals scaled to `[-1..1]`. The shape is `(stems, samples, channels)`.

#### Reading individual streams

Individual substreams of the stem file can be read by passing the corresponding stem id (starting from 0):

```python
S, rate = stempeg.read_stems(stempeg.example_stem_path(), stem_id=[0, 1])
```

#### Read excerpts (set seek position)

Excerpts from the stem instead of the full file can be read by providing start (`start`) and duration (`duration`) in seconds to `read_stems`:

```python
S, _ = stempeg.read_stems(stempeg.example_stem_path(), start=1, duration=1.5)
# read from second 1.0 to second 2.5
```

### Writing stems

Writing stem files from a numpy tensor

```python
stempeg.write_stems(path="output.stem.mp4", data=S, sample_rate=44100)
```

> :warning: __Warning__: Muxing stems using _ffmpeg_ leads to multi-stream files not compatible with Native Instrument Hardware or Software. Please use [MP4Box](https://github.com/gpac/gpac) and use the `stempeg.NISTemsWriter()`

### Use the command line tools

_stempeg_ provides a convenient cli tool to convert a stem to multiple wavfiles. The `-s` switch sets the start, the `-t` switch sets the duration.

```bash
stem2wav The Easton Ellises - Falcon 69.stem.mp4 -s 1.0 -t 2.5
```

## F.A.Q

#### How can I improve the reading performance?

`read_stems` is called repeatedly, it always does two system calls, one for getting the file info and one for the actual readingTo speed this up you could provide the `Info` object to `read_stems` if the number of streams, the number of channels and the samplerate is identical.

```python
file_path = stempeg.example_stem_path()
info = stempeg.Info(file_path)
S, _ = stempeg.read_stems(file_path, info=info)
```

#### How can the quality of the encoded stems be increased

For __Encoding__ it is recommended to use the Fraunhofer AAC encoder (`libfdk_aac`) which is not included in the default ffmpeg builds. Note that the conda version currently does _not_ include `fdk-aac`. If `libfdk_aac` is not installed _stempeg_ will use the default `aac` codec which will result in slightly inferior audio quality.
