#! /usr/bin/env python
import chunk
import filecmp
import hashlib
import os
import subprocess

try:
    import mutagenwrapper
except ImportError:
    mutagenwrapper = None


__version__ = '0.2'


#: Supported audio formats
AUDIO_FORMATS = ['flac', 'm4a', 'mp3']

#: Default `ffmpeg` path
FFMPEG_BIN = 'ffmpeg'


def equal(name1, name2, ffmpeg_bin=None):
    """
    Compares two files and returns True if they are considered equal. For audio
    files, they are equal if their uncompressed audio streams and tags
    (reported by mutagenwrapper, except for `encodedby` which is ignored) are
    equal. Otherwise, two files must have the same content to be equal.

    """
    if is_supported_format(name1) and is_supported_format(name2):
        return audio_equal(name1, name2, ffmpeg_bin) and tags_equal(name1, name2)
    else:
        return filecmp.cmp(name1, name2, False)


def audio_equal(name1, name2, ffmpeg_bin=None):
    """
    Compares two audio files and returns True if they have the same audio
    streams.

    """
    return checksum(name1, ffmpeg_bin) == checksum(name2, ffmpeg_bin)


def tags_equal(name1, name2):
    """
    Compares two audio files and returns True if they have the same tags
    reported by mutagenwrapper. It ignores `encodedby` tag.

    """
    return tags(name1) == tags(name2)


def checksum(name, ffmpeg_bin=None):
    """
    Returns an MD5 checksum of the uncompressed WAVE data stream of the audio
    file.

    """
    if ffmpeg_bin is None:
        ffmpeg_bin = ffmpeg_path()
    args = [ffmpeg_bin,
        '-i', '-',       # input from stdin
        '-vn',           # disable video recording
        '-f', 'wav',     # output format
        '-'              # output to stdout
    ]
    with open(name, 'rb') as f, open(os.devnull, 'wb') as fnull:
        proc = subprocess.Popen(args, stdin=f, stdout=subprocess.PIPE, stderr=fnull)
        _seek_to_data_chunk(proc.stdout)
        return _compute_md5(proc.stdout)


def _seek_to_data_chunk(f):
    assert f.read(12) == 'RIFF\x00\x00\x00\x00WAVE'
    while True:
        c = chunk.Chunk(f, bigendian=False)
        if c.getname() == 'data':
            break
        else:
            c.skip()


def _compute_md5(f):
    hasher = hashlib.md5()
    while True:
        data = f.read(hasher.block_size * 128)
        if not data:
            break
        hasher.update(data)
    return hasher.hexdigest()


def tags(name):
    """
    Returns tags in the audio file as `dict`. It converts tags returned by
    ``mutagenwrapper.read_tags`` by unwrapping single valued items
    (i.e. without enclosing lists) and removing `encodedby` tag. To read
    unmodified, but still normalized tags, use ``mutagenwrapper.read_tags``.
    For unmodified and unnormalized tags, use the ``mutagen`` library.

    """
    if mutagenwrapper is None:
        raise ImportError('mutagenwrapper is required to read tags')
    return {key: _unwrap(value)
            for key, value in mutagenwrapper.read_tags(name).iteritems()
            if key != 'encodedby'}


def _unwrap(x):
    n = len(x)
    if n == 0:
        return None
    elif n == 1:
        return x[0]
    else:
        return x


def is_supported_format(name):
    """
    Returns True if the name has an extension that is one of the supported
    formats.

    """
    parts = name.rsplit('.', 1)
    return len(parts) == 2 and parts[1] in AUDIO_FORMATS


def ffmpeg_path():
    """Returns the path to `ffmpeg` binary."""
    return os.environ.get('FFMPEG_BIN', FFMPEG_BIN)
