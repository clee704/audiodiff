#! /usr/bin/env python
from __future__ import print_function
from StringIO import StringIO
import argparse
import os
import sys
import traceback

import audiotools
import mutagen.flac
import mutagen.mp4

if sys.stdout.isatty():
    from termcolor import colored, cprint
else:
    colored = lambda *args: args[0]
    cprint = print


__version__ = '0.0.1'


#: Files with these extensions will treated as audio files.
#: Their audio streams and tags are compared if their filenames
#: match.
AUDIOFILE_EXTENSIONS = ['flac', 'm4a']


def main_func():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', metavar='FILE', nargs=2, type=Path,
        help='files or directories to compare. When comparing two directories, audio files with the same name (extensions may differ) will be compared.')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='verbosely list files processed')
    args = parser.parse_args()
    recursivediff(*args.files, verbose=args.verbose)


def recursivediff(p1, p2, verbose=False):
    "Compare paths p1 and p2 recursively."
    try:
        _recursivediff_wrapped(p1, p2, verbose)
    except Exception as e:
        print('An error occurred during processing {0} and {1}'.format(p1, p2))
        traceback.print_exc()


def _recursivediff_wrapped(p1, p2, verbose=False):
    if p1.isfile():
        if p2.isfile():
            filediff(p1, p2, verbose)
        else:
            print('{0} is a file and {1} is not'.format(p1, p2))
    elif p1.isdir():
        if p2.isdir():
            entries1 = [Path(e, hideext=True) for e in sorted(p1.listdir())]
            entries2 = [Path(e, hideext=True) for e in sorted(p2.listdir())]
            for entry1, entry2 in diffzip(entries1, entries2):
                if entry1 is None:
                    print('Only in {0}: {1}'.format(p2, entry2))
                elif entry2 is None:
                    print('Only in {0}: {1}'.format(p1, entry1))
                else:
                    recursivediff(p1.join(entry1), p2.join(entry2), verbose)
        else:
            print('{0} is a directory and {1} is not'.format(p1, p2))
    else:
        print('Either {0} or {1} is not a file or a directory'.format(p1, p2))


def filediff(p1, p2, verbose=False):
    "Compare files given by paths p1 and p2."
    if p1.isaudiofile() and p2.isaudiofile():
        streamdiff(p1, p2, verbose)
        tagdiff(p1, p2, verbose)
    else:
        binarydiff(p1, p2, verbose)


def streamdiff(p1, p2, verbose=False):
    "Compare the audio streams in two files."
    f1 = audiotools.open(p1.path)
    f2 = audiotools.open(p2.path)
    diff = not audiotools.pcm_cmp(f1.to_pcm(), f2.to_pcm())
    if diff:
        print('Audio streams in {0} and {1} differ'.format(p1.path, p2.path))
    elif verbose:
        print('Audio streams in {0} and {1} are equal'.format(p1.path, p2.path))


def tagdiff(p1, p2, verbose=False):
    "Compare the metadata of two files."
    pass


def binarydiff(p1, p2, verbose=False):
    "Compare the content of two files."
    # Using nested with statements to workaround the sphinx issue
    # https://bitbucket.org/birkenfeld/sphinx/issue/1102
    with open(p1.path) as f1:
        with open(p2.path) as f2:
            diff = f1.read() != f2.read()
    if diff:
        print('Binary file {0} and {1} differ'.format(p1.path, p2.path))
    elif verbose:
        print('Binary file {0} and {1} are equal'.format(p1.path, p2.path))


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
        "Return *True* if the path ends with :const:`AUDIOFILE_EXTENSIONS`."
        return self.ext is not None

    def hideext(self):
        "Hide the audio file extension."
        self._exthidden = True

    def showext(self):
        "Show the audio file extension."
        self._exthidden = False

    def isfile(self):
        "Return *True* if the path is an existing regular file."
        return os.path.isfile(self.path)

    def isdir(self):
        "Return *True* if the path is an existing directory."
        return os.path.isdir(self.path)

    def join(self, *paths):
        "Join one or more path components intelligently."
        return Path(os.path.join(self.path, *(p.path for p in paths)))

    def listdir(self):
        "Return a list containing the names of the entries in the the path."
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
