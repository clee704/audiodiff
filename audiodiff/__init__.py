#! /usr/bin/env python
from __future__ import print_function
from operator import itemgetter
import argparse
import os
import re
import sys
import traceback

from mutagenwrapper import open_tags
from pydub import AudioSegment

if sys.stdout.isatty():
    from termcolor import colored, cprint
else:
    colored = lambda *args: args[0]
    cprint = print


__version__ = '0.0.2'


#: Files with these extensions will treated as audio files.
#: Their audio streams and tags are compared if their filenames
#: match.
AUDIOFILE_EXTENSIONS = ['flac', 'm4a', 'mp3']


def main_func():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', metavar='FILE', nargs=2, type=Path,
        help='Files or directories to compare. When comparing two directories, audio files with the same name (extensions may differ) will be compared.')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='Verbosely list files processed')
    parser.add_argument('-s', '--streams', action='store_true',
        help='Compare only streams')
    parser.add_argument('-t', '--tags', action='store_true',
        help='Compare only tags. This is useful since the comparison is very slow')
    args = parser.parse_args()
    try:
        recursivediff(*args.files, verbose=args.verbose, tags_only=args.tags, streams_only=args.streams)
    except KeyboardInterrupt:
        print('Interrupted')


def recursivediff(p1, p2, verbose=False, tags_only=False, streams_only=False):
    "Compares paths p1 and p2 recursively."
    try:
        _recursivediff_wrapped(p1, p2, verbose, tags_only, streams_only)
    except Exception as e:
        print('An error occurred during processing {0} and {1}'.format(p1.path, p2.path))
        traceback.print_exc()


def _recursivediff_wrapped(p1, p2, verbose=False, tags_only=False, streams_only=False):
    if p1.isfile():
        if p2.isfile():
            filediff(p1, p2, verbose, tags_only, streams_only)
        else:
            print('{0} is a file and {1} is not'.format(p1.path, p2.path))
    elif p1.isdir():
        if p2.isdir():
            entries1 = [Path(e, hideext=True) for e in sorted(p1.listdir())]
            entries2 = [Path(e, hideext=True) for e in sorted(p2.listdir())]
            for entry1, entry2 in diffzip(entries1, entries2):
                if entry1 is None:
                    print('Only in {0}: {1}'.format(p2.path, entry2.path))
                elif entry2 is None:
                    print('Only in {0}: {1}'.format(p1.path, entry1.path))
                else:
                    recursivediff(p1.join(entry1), p2.join(entry2), verbose, tags_only, streams_only)
        else:
            print('{0} is a directory and {1} is not'.format(p1.path, p2.path))
    else:
        print('Either {0} or {1} is not a file or a directory'.format(p1.path, p2.path))


def filediff(p1, p2, verbose=False, tags_only=False, streams_only=False):
    "Compares files given by paths p1 and p2."
    if p1.isaudiofile() and p2.isaudiofile():
        if tags_only:
            tagdiff(p1, p2, verbose)
        elif streams_only:
            streamdiff(p1, p2, verbose)
        else:
            streamdiff(p1, p2, verbose)
            tagdiff(p1, p2, verbose)
    else:
        binarydiff(p1, p2, verbose)


def streamdiff(p1, p2, verbose=False):
    "Compares the audio streams in two files."
    song1 = AudioSegment.from_file(p1.path)
    song2 = AudioSegment.from_file(p2.path)
    if not (song1 == song2):  # pydub bug prevents use of !=
        print('Audio streams in {0} and {1} differ'.format(p1.path, p2.path))
    elif verbose:
        print('Audio streams in {0} and {1} are equal'.format(p1.path, p2.path))


def tagdiff(p1, p2, verbose=False):
    "Compares the metadata of two files."
    tags1 = open_tags(p1.path)
    tags2 = open_tags(p2.path)
    same, data = dict_cmp(tags1, tags2)
    if not same:
        colors = {'-': 'red', '+': 'green', ' ': None}
        cprint(colored('--- {0}'.format(p1.path), colors['-']))
        cprint(colored('+++ {0}'.format(p2.path), colors['+']))
        for sign, key, value in data:
            if sign == ' ' and not verbose:
                continue
            value = str(value)
            if len(value) > 100:
                value = value[:92] + '...' + value[-5:]
            cprint(colored('{0}{1}: {2}'.format(sign, key, value), colors[sign]))
    elif verbose:
        print('Tags in {0} and {1} are equal'.format(p1.path, p2.path))


def binarydiff(p1, p2, verbose=False):
    "Compares the content of two files."
    # Using nested with statements to workaround the sphinx issue
    # https://bitbucket.org/birkenfeld/sphinx/issue/1102
    with open(p1.path) as f1:
        with open(p2.path) as f2:
            diff = f1.read() != f2.read()
    if diff:
        print('Binary files {0} and {1} differ'.format(p1.path, p2.path))
    elif verbose:
        print('Binary files {0} and {1} are equal'.format(p1.path, p2.path))


def diffzip(list1, list2):
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


def dict_cmp(dict1, dict2):
    """
    Compares two dictionary-like objects and returns a tuple. The first
    item of the tuple is *True* if the two objects have the same set of
    keys and values, otherwise *False*. The second item is a list
    of tuples (*sign*, *key*, *value*). *sign* is '-' if the key is present
    in the first object but not in the second, or the key is present in
    both objects but the values differ. A '+' sign means the opposite.
    A ' ' sign means the key and value are present in both objects.

    Examples:

    >>> dict_cmp({'a': 1, 'b': 2, 'c': 3}, {'b': 2, 'c': 5, 'd': 7})
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


class Path(object):
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
        for ext in AUDIOFILE_EXTENSIONS:
            if path.endswith(ext):
                self._path_without_ext = path[:-len(ext) - 1]
                self.ext = ext
        self._exthidden = hideext

    def isaudiofile(self):
        "Returns *True* if the path ends with :const:`AUDIOFILE_EXTENSIONS`."
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
        return Path(os.path.join(self.path, *(p.path for p in paths)))

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


if __name__ == '__main__':
    main_func()
