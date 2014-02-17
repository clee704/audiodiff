#! /usr/bin/env python
"""
   audiodiff
   ~~~~~~~~~

   This module contains functions for comparing audio files.

"""
import chunk
import filecmp
import hashlib
import os
import subprocess

try:
    import mutagenwrapper
except ImportError:
    mutagenwrapper = None


__version__ = '0.3.0'


#: Supported audio formats (extensions)
AUDIO_FORMATS = ['wav', 'flac', 'm4a', 'mp3']

#: Default FFmpeg path
FFMPEG_BIN = 'ffmpeg'


def equal(name1, name2, ffmpeg_bin=None):
    """Compares two files and returns ``True`` if they are considered equal.
    For audio files, they are equal if their uncompressed audio streams and
    tags (as reported by mutagenwrapper, except for ``encodedby`` which is
    ignored) are equal. For non-audio files, they must have the same content to
    be equal.

    """
    if is_supported_format(name1) and is_supported_format(name2):
        return audio_equal(name1, name2, ffmpeg_bin) and tags_equal(name1,
                                                                    name2)
    else:
        return filecmp.cmp(name1, name2, False)


def audio_equal(name1, name2, ffmpeg_bin=None):
    """Compares two audio files and returns ``True`` if they have the same
    audio streams.

    """
    return checksum(name1, ffmpeg_bin) == checksum(name2, ffmpeg_bin)


def tags_equal(name1, name2):
    """Compares two audio files and returns ``True`` if they have the same tags
    reported by mutagenwrapper.

    """
    return tags(name1) == tags(name2)


def checksum(name, ffmpeg_bin=None):
    """Returns an SHA1 checksum of the uncompressed PCM (signed 24-bit
    little-endian) data stream of the audio file. Note that the checksums for
    the same file may differ across different platforms if the file format is
    lossy, due to floating point problems and different implementations of
    decoders.

    """
    if ffmpeg_bin is None:
        ffmpeg_bin = ffmpeg_path()
    args = [
        ffmpeg_bin,
        '-i', name,
        '-vn',
        '-f', 's24le',
        '-',
    ]

    # Check if the file is readable and raise an appropriate exception if not
    with open(name) as f:
        f.read(1)

    with open(os.devnull, 'wb') as fnull:
        proc = subprocess.Popen(args, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        sha1sum = _compute_sha1(proc.stdout)
        proc.wait()
        try:
            if sha1sum is None:
                raise ExternalLibraryError(proc.stderr.read())
            return sha1sum
        finally:
            proc.stdout.close()
            proc.stderr.close()


def _compute_sha1(f):
    hasher = hashlib.sha1()
    empty = True
    while True:
        data = f.read(hasher.block_size * 128)
        if not data:
            break
        empty = False
        hasher.update(data)
    if empty:
        return None
    return hasher.hexdigest()


def tags(name):
    """Returns tags in the audio file as a :class:`dict`. Its return value is
    the same as ``mutagenwrapper.read_tags``, except that single valued items
    (lists with length 1) are unwrapped and ``encodedby`` tag is removed. To
    read unmodified, but still normalized tags, use
    ``mutagenwrapper.read_tags``. For raw tags, use the ``mutagen`` library.

    """
    if mutagenwrapper is None:
        raise ImportError('mutagenwrapper is required to read tags')
    if not is_supported_format(name):
        raise UnsupportedFileError(name + ' is not a supported audio file')
    if get_extension(name) == 'wav':
        return {}
    return dict((key, _unwrap(value))
                for key, value in mutagenwrapper.read_tags(name).iteritems()
                if key != 'encodedby')


def _unwrap(x):
    n = len(x)
    if n == 0:
        return None
    elif n == 1:
        return x[0]
    else:
        return x


def get_extension(path):
    """
    Returns the file extension of the specified path. Example::

        >>> get_extension('a.pdf')
        'pdf'
        >>> get_extension('b.js.coffee')
        'coffee'
        >>> get_extension('c')
        ''
        >>> get_extension('d/e.txt')
        'txt'

    """
    parts = os.path.basename(path).rsplit('.', 1)
    return parts[1] if len(parts) > 1 else ''


def is_supported_format(path):
    """Returns True if the specified path has an extension that is one of the
    supported formats.

    """
    return get_extension(path) in AUDIO_FORMATS


def ffmpeg_path():
    """Returns the path to FFmpeg binary."""
    return os.environ.get('FFMPEG_BIN', FFMPEG_BIN)


class AudiodiffException(Exception):
    """The root class of all audiodiff-related exceptions."""


class UnsupportedFileError(AudiodiffException):
    """Raised when you pass a non-audio file to a function that expects audio
    files.

    """


class ExternalLibraryError(AudiodiffException):
    """Raised when there is an error during running FFmpeg."""
