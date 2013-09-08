#! /usr/bin/env python
from __future__ import print_function
import argparse
from chunk import Chunk
import hashlib
from operator import itemgetter
import os
import re
from StringIO import StringIO
import struct
import subprocess
import sys
import traceback

from mutagenwrapper import open_tags

if sys.stdout.isatty():
    from termcolor import colored, cprint
else:
    colored = lambda *args: args[0]
    cprint = print


__version__ = '0.1.0'


#: Supported audio formats
AUDIO_FORMATS = ['flac', 'm4a', 'mp3']
FFMPEG_BIN = 'ffmpeg'


def ffmpeg_path():
    """Returns the path to ffmpeg binary."""
    return os.environ.get('FFMPEG_BIN', FFMPEG_BIN)


def getaudiostream(filepath, ffmpeg_bin=None):
    """
    Returns the uncompressed WAV stream of the audio file.

    """
    if ffmpeg_bin is None:
        ffmpeg_bin = ffmpeg_path()
    args = [ffmpeg_bin,
        '-i', filepath,  # input from path
        '-vn',           # disable video recording
        '-f', 'wav',     # output format
        '-'              # output to stdout
    ]
    with open(os.devnull, 'w') as fnull:
        raw_wave_data = subprocess.check_output(args, stderr=fnull)
        return _readframes(raw_wave_data)


def _readframes(raw_wave_data):
    """
    Returns wave data frames. ffmpeg gives zero chunk sizes when it outputs to
    standard out, so the `wave` standard library cannot read the output.

    """
    # Write RIFF chunk size
    temp = []
    temp.append(raw_wave_data[:4])
    assert raw_wave_data[4:8] == '\x00\x00\x00\x00'
    temp.append(struct.pack('<L', len(raw_wave_data) - 8))
    temp.append(raw_wave_data[8:])
    # Find data chunk offset
    f = Chunk(StringIO(''.join(temp)), bigendian=False)
    assert f.getname() == 'RIFF'
    assert f.read(4) == 'WAVE'
    while True:
        try:
            chunk = Chunk(f, bigendian=False)
        except EOFError:
            break
        if chunk.getname() == 'data':
            offset = f.tell() + 8
            break
        else:
            chunk.skip()
    return raw_wave_data[offset:]


def checksum(filepath):
    """
    Returns the MD5 checksum of the uncompressed WAV stream of the audio file.

    """
    return hashlib.md5(getaudiostream(filepath)).hexdigest()


def issupportedformat(filepath):
    """
    Returns True if the filepath has an extension that is one of the supported
    formats.

    """
    parts = filepath.rsplit('.', 1)
    return len(parts) == 2 and parts[1] in AUDIO_FORMATS


def audioequal(filepath1, filepath2):
    """
    Compares two audio files and returns True if they have the same audio
    streams.

    """
    return getaudiostream(filepath1) == getaudiostream(filepath2)


def tagsequal(filepath1, filepath2):
    """
    Compares two audio files and returns True if they have the same tags
    reported by mutagenwrapper. It ignores `encodedby` tag.

    """
    tags1 = open_tags(filepath1)
    tags2 = open_tags(filepath2)
    if 'encodedby' in tags1: del tags1['encodedby']
    if 'encodedby' in tags2: del tags2['encodedby']
    print(sorted(tags1.iteritems()))
    print(sorted(tags2.iteritems()))
    return sorted(tags1.iteritems()) == sorted(tags2.iteritems())


def equal(filepath1, filepath2):
    """
    Compares two files and returns True if they are considered equal. For audio
    files, they are equal if audio streams and tags (reported by mutagenwrapper)
    are equal. Otherwise, two files must have the same content to be equal.

    """
    if issupportedformat(filepath1) and issupportedformat(filepath2):
        return (audioequal(filepath1, filepath2) and
                tagsequal(filepath1, filepath2))
    else:
        with open(filepath1) as f1, open(filepath2) as f2:
            return f1.read() == f2.read()


def tags(filepath):
    """
    Returns tags in the audio file. It wraps ``mutagenwrapper.open_tags`` and
    returns all values in a new `dict` with single valued items unwrapped
    (i.e. without enclosing lists). `encodedby` tag is not returned by default.
    To read that tag, use ``mutagenwrapper.open_tags``.

    """
    tags = {}
    for key, value in open_tags(filepath).iteritems():
        if key == 'encodedby':
            continue
        if len(value) == 1:
            value = value[0]
        tags[key] = value
    return tags


def tagsdiff(filepath1, filepath2, verbose=False):
    """
    Prints different tags in the two audio files.

    """
    tags1 = tags(filepath1)
    tags2 = tags(filepath2)
    same, data = dictcmp(tags1, tags2)
    if not same:
        colors = {'-': 'red', '+': 'green', ' ': None}
        cprint(colored('--- {0}'.format(filepath1), colors['-']))
        cprint(colored('+++ {0}'.format(filepath2), colors['+']))
        for sign, key, value in data:
            if sign == ' ' and not verbose:
                continue
            value = str(value)
            if len(value) > 100:
                value = value[:92] + '...' + value[-5:]
            cprint(colored('{0}{1}: {2}'.format(sign, key, value),
                   colors[sign]))
    elif verbose:
        print('Tags in {0} and {1} are equal'.format(filepath1, filepath2))


def dictcmp(dict1, dict2):
    """
    Compares two dictionary-like objects and returns a tuple. The first
    item of the tuple is *True* if the two objects have the same set of
    keys and values, otherwise *False*. The second item is a list
    of tuples (*sign*, *key*, *value*). *sign* is '-' if the key is present
    in the first object but not in the second, or the key is present in
    both objects but the values differ. A '+' sign means the opposite.
    A ' ' sign means the key and value are present in both objects.

    Examples:

    >>> dictcmp({'a': 1, 'b': 2, 'c': 3}, {'b': 2, 'c': 5, 'd': 7})
    (False, [('-', 'a', 1), (' ', 'b', 2), ('-', 'c', 3), ('+', 'c', 5), ('+', 'd', 7)])

    """
    keys1 = set(dict1.keys())
    keys2 = set(dict2.keys())
    data = []
    for key in keys1 - keys2:
        data.append(('-', key, dict1[key]))
    for key in keys2 - keys1:
        data.append(('+', key, dict2[key]))
    for key in keys1 & keys2:
        if dict1[key] != dict2[key]:
            data.append(('-', key, dict1[key]))
            data.append(('+', key, dict2[key]))
        else:
            data.append((' ', key, dict1[key]))
    data.sort(key=itemgetter(1))
    return not any(t[0] != ' ' for t in data), data


class CommandlineTool(object):

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('files',
            metavar='file',
            nargs=2,
            type=_Path,
            help='Files or directories to compare. When comparing two '
                 'directories, audio files with the same name (extensions may '
                 'differ) will be compared.')
        parser.add_argument('-v', '--verbose',
            action='store_true',
            help='Verbosely list files processed')
        parser.add_argument('-a', '--streams',
            action='store_true',
            help='Compare only streams')
        parser.add_argument('-t', '--tags',
            action='store_true',
            help='Compare only tags. This is useful since comparing audio '
                 'streams could be slow.')
        parser.add_argument('--ffmpeg_bin',
            metavar='path',
            help='Specify ffmpeg binary path')
        self.parser = parser

    def run(self):
        args = self.parser.parse_args()
        try:
            self._diff_recurse(args.files[0], args.files[1], args)
        except KeyboardInterrupt:
            print('Interrupted')

    def _diff_recurse(self, p1, p2, args):
        "Compares paths p1 and p2 recursively."
        try:
            self._diff_recurse_2(p1, p2, args)
        except Exception as e:
            print('An error occurred during processing {0} and {1}'.format(
                    p1.path, p2.path))
            traceback.print_exc()

    def _diff_recurse_2(self, p1, p2, args):
        p = (p1.path, p2.path)
        if p1.isfile():
            if p2.isfile():
                self._diff_file(p1, p2, args)
            else:
                print('{0} is a file and {1} is not'.format(*p))
        elif p1.isdir():
            if p2.isdir():
                es1 = [_Path(e, hideext=True) for e in sorted(p1.listdir())]
                es2 = [_Path(e, hideext=True) for e in sorted(p2.listdir())]
                for entry1, entry2 in _diffzip(es1, es2):
                    if entry1 is None:
                        print('Only in {0}: {1}'.format(p2.path, entry2.path))
                    elif entry2 is None:
                        print('Only in {0}: {1}'.format(p1.path, entry1.path))
                    else:
                        self._diff_recurse(p1.join(entry1), p2.join(entry2),
                                args)
            else:
                print('{0} is a directory and {1} is not'.format(*p))
        else:
            print('Either {0} or {1} is not a file or a directory'.format(*p))

    def _diff_file(self, p1, p2, args):
        "Compares files given by paths p1 and p2."
        if p1.isaudiofile() and p2.isaudiofile():
            if args.tags:
                tagsdiff(p1.path, p2.path, args.verbose)
            elif args.streams:
                self._diff_streams(p1, p2, args)
            else:
                self._diff_streams(p1, p2, args)
                tagsdiff(p1.path, p2.path, args.verbose)
        else:
            self._diff_binary(p1, p2, args)

    def _diff_streams(self, p1, p2, args):
        "Compares the audio streams in two files."
        p = (p1.path, p2.path)
        song1 = getaudiostream(p1.path, args.ffmpeg_bin)
        song2 = getaudiostream(p2.path, args.ffmpeg_bin)
        if song1 != song2:
            print('Audio streams in {0} and {1} differ'.format(*p))
        elif args.verbose:
            print('Audio streams in {0} and {1} are equal'.format(*p))

    def _diff_binary(self, p1, p2, args):
        "Compares the content of two files."
        # Using nested with statements to workaround the sphinx issue
        # https://bitbucket.org/birkenfeld/sphinx/issue/1102
        p = (p1.path, p2.path)
        with open(p1.path) as f1:
            with open(p2.path) as f2:
                differ = f1.read() != f2.read()
        if differ:
            print('Binary files {0} and {1} differ'.format(*p))
        elif args.verbose:
            print('Binary files {0} and {1} are equal'.format(*p))


class _Path(object):
    """
    Path object with an ability to show or hide the audio file extension.
    When the extension is hidden, :meth:`__str__()` returns the
    path with the extension stripped off.

    .. attribute:: path

       Actual path

    .. attribute:: ext

       Audio file extension (*None* if not an audio file)

    """

    def __init__(self, path, hideext=False):
        self.path = path
        self._path_without_ext = path
        self.ext = None
        for ext in AUDIO_FORMATS:
            if path.endswith(ext):
                self._path_without_ext = path[:-len(ext) - 1]
                self.ext = ext
        self._exthidden = hideext

    def isaudiofile(self):
        "Returns *True* if the path ends with :const:`AUDIO_FORMATS`."
        return self.ext is not None

    def hideext(self):
        "Hides the audio file extension."
        self._exthidden = True

    def showext(self):
        "Shows the audio file extension."
        self._exthidden = False

    def isfile(self):
        "Returns *True* if the path is an existing regular file."
        return os.path.isfile(self.path)

    def isdir(self):
        "Returns *True* if the path is an existing directory."
        return os.path.isdir(self.path)

    def join(self, *paths):
        "Joins one or more path components intelligently."
        return _Path(os.path.join(self.path, *(p.path for p in paths)))

    def listdir(self):
        "Returns a list containing the names of the entries in the the path."
        return os.listdir(self.path)

    def __str__(self):
        return self.path if not self._exthidden else self._path_without_ext

    def __lt__(self, other):
        return str(self) < str(other)

    def __le__(self, other):
        return str(self) <= str(other)

    def __eq__(self, other):
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)

    def __gt__(self, other):
        return str(self) > str(other)

    def __ge__(self, other):
        return str(self) >= str(other)


def _diffzip(list1, list2):
    """
    Returns a list of tuples that aggregates elements from each list.
    Each list must be sorted so that ``a <= b`` for every pair of
    adjacent elements (``a``, ``b``).

    Examples:

    >>> diffzip(['a', 'b', 'c', 'e'], ['b', 'd', 'e'])
    [('a', None), ('b', 'b'), ('c', None), (None, 'd'), ('e', 'e')]

    """
    rv = []
    n = len(list1)
    m = len(list2)
    i = j = 0
    while i < n and j < m:
        elem1 = list1[i]
        elem2 = list2[j]
        if elem1 < elem2:
            rv.append((elem1, None))
            i += 1
        elif elem1 > elem2:
            rv.append((None, elem2))
            j += 1
        else:
            rv.append((elem1, elem2))
            i += 1
            j += 1
    while i < n:
        rv.append((list1[i], None))
        i += 1
    while j < m:
        rv.append((None, list2[j]))
        j += 1
    return rv


if __name__ == '__main__':
    CommandlineTool().run()
