"""
   audiodiff.commandlinetool
   ~~~~~~~~~~~~~~~~~~~~~~~~~

   This module contains functions for the ``audiodiff`` commandline tool.

"""
import argparse
import itertools
import locale
import operator
import os
import sys
import traceback

try:
    import termcolor
except ImportError:
    termcolor = None

from . import __version__, is_supported_format, equal, audio_equal, tags


if sys.stdout.isatty() and termcolor is not None:
    colored = termcolor.colored
else:
    colored = lambda *options: options[0]


#: Fallback encoding for output. Encoding resolution is done as follows:
#:
#: - :data:`sys.stdout.encoding` (or :data:`sys.stderr.encoding`)
#: - ``PYTHONIOENCODING`` environment variable
#: - Second item of the return value of :func:`locale.getdefaultlocale`
#: - :data:`FALLBACK_ENCODING`
FALLBACK_ENCODING = 'UTF-8'

LOCALE_ENCODING = locale.getdefaultlocale()[1]


#: An :class:`argparse.ArgumentParser`
parser = argparse.ArgumentParser(
    prog='audiodiff',
    description="""
Compare two files or directories recursively. For supported audio files
(flac, m4a, mp3), they are treated as if extensions are removed from filenames.
For example, `audiodiff x y` would compare `x/a.flac` and `y/a.m4a`. Audio
files are considered equal if they have the same uncompressed audio streams and
normalized tags (except for `encodedby` tag) reported by mutagenwrapper;
non-audio files as well as unsupported audio files are equal if they are
exactly equal, bit by bit.
""".format(__version__),
    epilog='version {0}'.format(__version__))
parser.add_argument(
    'files',
    metavar='file',
    nargs=2,
    help='two files or directories to compare')
parser.add_argument(
    '-a', '--streams',
    action='store_true',
    help='compare only audio streams')
parser.add_argument(
    '-t', '--tags',
    action='store_true',
    help='compare only tags; '
         'useful since comparing audio streams could be slow')
parser.add_argument(
    '-q', '--brief',
    action='store_true',
    help='report only whether files differ')
parser.add_argument(
    '-s', '--report-identical-files',
    action='store_true',
    dest='verbose',
    help='report when two files are the same')
parser.add_argument(
    '--ffmpeg_bin',
    metavar='path',
    help='specify ffmpeg binary path')


def main_func(args=None):
    """The entry point for the ``audiodiff`` command line tool. Parses the
    command arguments and calls :func:`diff_checked`.

    """
    try:
        options = parser.parse_args(args)
        return diff_checked(options.files[0], options.files[1], options)
    except KeyboardInterrupt:
        return 130


def diff_checked(path1, path2, options):
    """Calls :func:`diff_recurse` and handles exceptions if raised."""
    try:
        return diff_recurse(path1, path2, options)
    except IOError as e:
        _print_error('{0}: {1}'.format(e.strerror, repr(e.filename)))
        return 2
    except Exception as e:
        _print_error('an error occurred while processing {0} and {1}'.format(
            repr(path1), repr(path2)))
        traceback.print_exc()
        return 2


def diff_recurse(path1, path2, options):
    """Recursively compares files in the specified paths."""
    type1 = _get_type(path1)
    type2 = _get_type(path2)
    if type1 == 'file' and type2 == 'file':
        return diff_files(path1, path2, options)
    elif type1 == 'dir' and type2 == 'dir':
        return diff_dirs(path1, path2, options)
    elif type1 == 'file' and type2 == 'dir':
        return diff_files(path1, os.path.join(path2, os.path.basename(path1)),
                          options)
    elif type1 == 'dir' and type2 == 'file':
        return diff_files(os.path.join(path2, os.path.basename(path1)), path2,
                          options)
    # errors
    if type1 == 'nonexistent':
        msg = "No such file or directory: {0}".format(repr(path1))
    elif type2 == 'nonexistent':
        msg = "No such file or directory: {0}".format(repr(path2))
    else:
        msg = 'Unknown files: {0} and/or {1}'.format(repr(path1), repr(path2))
    _print_error(msg)
    return 2


def _get_type(name):
    if os.path.isfile(name):
        return 'file'
    elif os.path.isdir(name):
        return 'dir'
    elif not os.path.exists(name):
        return 'nonexistent'


def diff_files(path1, path2, options):
    """Compares the two files and prints the results."""
    if is_supported_format(path1) and is_supported_format(path2):
        if options.streams:
            return diff_streams(path1, path2, options.verbose,
                                options.ffmpeg_bin)
        elif options.tags:
            return diff_tags(path1, path2, options.verbose, options.brief)
        else:
            return max(diff_streams(path1, path2, options.verbose,
                                    options.ffmpeg_bin),
                       diff_tags(path1, path2, options.verbose, options.brief))
    else:
        return diff_binary(path1, path2, options.verbose)


def diff_dirs(path1, path2, options):
    """Compares the two directories and prints the results."""
    ret = 0
    cnames1 = _cnames(path1)
    cnames2 = _cnames(path2)
    for cname in sorted(set(cnames1.iterkeys()) | set(cnames2.iterkeys())):
        names1 = cnames1.get(cname)
        names2 = cnames2.get(cname)
        if not names1:
            for name in names2:
                _print(u'Only in {0}: {1}'.format(_decode_path(path2),
                                                  _decode_path(name)))
                ret = max(ret, 1)
        elif not names2:
            for name in names1:
                _print(u'Only in {0}: {1}'.format(_decode_path(path1),
                                                  _decode_path(name)))
                ret = max(ret, 1)
        else:
            for name1, name2 in itertools.product(names1, names2):
                np1 = os.path.join(path1, name1)
                np2 = os.path.join(path2, name2)
                ret = max(ret, diff_checked(np1, np2, options))
    return ret


def _cnames(d):
    names = os.listdir(d)
    names.sort()
    cnames = {}
    for name in names:
        if is_supported_format(name):
            cname = name.rsplit('.', 1)[0]
            cnames.setdefault(cname, []).append(name)
        else:
            cnames[name] = [name]
    return cnames


def diff_streams(path1, path2, verbose=False, ffmpeg_bin=None):
    """Prints whether the two audio files' streams differ or are identical."""
    if not audio_equal(path1, path2, ffmpeg_bin):
        _print(u'Audio streams in {0} and {1} differ'.format(
            _decode_path(path1), _decode_path(path2)))
        return 1
    elif verbose:
        _print(u'Audio streams in {0} and {1} are identical'.format(
            _decode_path(path1), _decode_path(path2)))
    return 0


def diff_tags(path1, path2, verbose=False, brief=False):
    """Prints whether the two audio files' tags differ or are identical."""
    tags1 = tags(path1)
    tags2 = tags(path2)
    if tags1 == tags2:
        if verbose:
            _print(u'Tags in {0} and {1} are identical'.format(
                _decode_path(path1), _decode_path(path2)))
        return 0
    if brief:
        _print(u'Tags in {0} and {1} differ'.format(
            _decode_path(path1), _decode_path(path2)))
        return 1
    data = _compare_dicts(tags1, tags2)
    colors = {'-': 'red', '+': 'green', ' ': None}
    _print(colored(u'--- {0}'.format(_decode_path(path1)), colors['-']))
    _print(colored(u'+++ {0}'.format(_decode_path(path2)), colors['+']))
    for sign, key, value in data:
        if sign == ' ' and not verbose:
            continue
        if not isinstance(value, unicode):
            value = repr(value)
        if len(value) > 100:
            value = value[:92] + '...' + value[-5:]
        _print(colored(u'{0}{1}: {2}'.format(sign, key, value), colors[sign]))
    return 1


def _compare_dicts(dict1, dict2):
    """Compares two dictionary-like objects and returns a list of tuples
    (*sign*, *key*, *value*). *sign* is '-' if the key is present
    in the first object but not in the second, or the key is present in
    both objects but the values differ. A '+' sign means the opposite.
    A ' ' sign means the key and value are present in both objects.

    Examples::

        >>> compare_dicts({'a': 1, 'b': 2, 'c': 3}, {'b': 2, 'c': 5, 'd': 7})
        [('-', 'a', 1), (' ', 'b', 2), ('-', 'c', 3), ('+', 'c', 5),
         ('+', 'd', 7)]

    """
    keys1 = set(dict1.iterkeys())
    keys2 = set(dict2.iterkeys())
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
    data.sort(key=operator.itemgetter(1))
    return data


def diff_binary(path1, path2, verbose=False):
    """Prints whether the two non-audio files differ or are identical."""
    if not equal(path1, path2):
        _print(u'Files {0} and {1} differ'.format(_decode_path(path1),
                                                  _decode_path(path2)))
        return 1
    elif verbose:
        _print(u'Files {0} and {1} are identical'.format(_decode_path(path1),
                                                         _decode_path(path2)))
    return 0


# Due to a bug in Sphinx, we cannot use from __future__ import print_function
# https://bitbucket.org/birkenfeld/sphinx/issue/1385/sphinxpycodemoduleanalyzer-fails-with
def _print(message):
    print message.encode(_encoding_for(sys.stdout), 'replace')


def _print_error(message):
    print >>sys.stderr, '{0}: {1}'.format(
        parser.prog, message.encode(_encoding_for(sys.stderr), 'replace'))


def _encoding_for(file):
    return (file.encoding or os.environ.get('PYTHONIOENCODING') or
            LOCALE_ENCODING or FALLBACK_ENCODING)


def _decode_path(path):
    return path.decode(LOCALE_ENCODING or FALLBACK_ENCODING, 'replace')
