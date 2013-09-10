from __future__ import print_function
import argparse
import itertools
import operator
import os
import sys
import traceback

try:
    import termcolor
except ImportError:
    termcolor = None

from . import __version__, is_supported_format, equal, audio_equal, tags


parser = argparse.ArgumentParser(prog='audiodiff',
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
parser.add_argument('files',
    metavar='file',
    nargs=2,
    help='two files or directories to compare')
parser.add_argument('-a', '--streams',
    action='store_true',
    help='compare only audio streams')
parser.add_argument('-t', '--tags',
    action='store_true',
    help='compare only tags; useful since comparing audio streams could be slow')
parser.add_argument('-q', '--brief',
    action='store_true',
    help='report only whether files differ')
parser.add_argument('-s', '--report-identical-files',
    action='store_true',
    dest='verbose',
    help='report when two files are the same')
parser.add_argument('--ffmpeg_bin',
    metavar='path',
    help='specify ffmpeg binary path')


def main_func(args=None):
    try:
        options = parser.parse_args(args)
        return diff_checked(options.files[0], options.files[1], options)
    except KeyboardInterrupt:
        return 130


def diff_checked(p1, p2, options):
    try:
        return diff_recurse(p1, p2, options)
    except IOError as e:
        msg = '{0}: {1}: {2}'.format(parser.prog, e.strerror, repr(e.filename))
        print(msg, file=sys.stderr)
        return 2
    except Exception as e:
        msg = '{0}: an error occurred while processing {1} and {2}'.format(parser.prog, p1, p2)
        print(msg, file=sys.stderr)
        traceback.print_exc()
        return 2


def diff_recurse(p1, p2, options):
    type1 = _get_type(p1)
    type2 = _get_type(p2)
    if type1 == 'file' and type2 == 'file':
        return diff_files(p1, p2, options)
    elif type1 == 'dir' and type2 == 'dir':
        return diff_dirs(p1, p2, options)
    elif type1 == 'file' and type2 == 'dir':
        return diff_files(p1, os.path.join(p2, os.path.basename(p1)), options)
    elif type1 == 'dir' and type2 == 'file':
        return diff_files(os.path.join(p2, os.path.basename(p1)), p2, options)
    # errors
    if type1 == 'nonexistent':
        msg = "No such file or directory: {0}".format(repr(p1))
    elif type2 == 'nonexistent':
        msg = "No such file or directory: {0}".format(repr(p2))
    else:
        msg = 'Unknown files: {0} and/or {1}'.format(repr(p1), repr(p2))
    print('{0}: {1}'.format(parser.prog, msg), file=sys.stderr)
    return 2


def _get_type(name):
    if os.path.isfile(name):
        return 'file'
    elif os.path.isdir(name):
        return 'dir'
    elif not os.path.exists(name):
        return 'nonexistent'


def diff_files(p1, p2, options):
    if is_supported_format(p1) and is_supported_format(p2):
        if options.streams:
            return diff_streams(p1, p2, options.verbose, options.ffmpeg_bin)
        elif options.tags:
            return diff_tags(p1, p2, options.verbose, options.brief)
        else:
            return max(diff_streams(p1, p2, options.verbose, options.ffmpeg_bin),
                       diff_tags(p1, p2, options.verbose, options.brief))
    else:
        return diff_binary(p1, p2, options.verbose)


def diff_dirs(p1, p2, options):
    ret = 0
    cnames1 = _cnames(p1)
    cnames2 = _cnames(p2)
    for cname in sorted(set(cnames1.iterkeys()) | set(cnames2.iterkeys())):
        names1 = cnames1.get(cname)
        names2 = cnames2.get(cname)
        if not names1:
            for name in names2:
                print('Only in {0}: {1}'.format(p2, name))
                ret = max(ret, 1)
        elif not names2:
            for name in names1:
                print('Only in {0}: {1}'.format(p1, name))
                ret = max(ret, 1)
        else:
            for name1, name2 in itertools.product(names1, names2):
                np1 = os.path.join(p1, name1)
                np2 = os.path.join(p2, name2)
                ret = max(ret, diff_checked(np1, np2, options))
    return ret


def _cnames(d):
    names = os.listdir(d)
    cnames = {}
    for name in names:
        if is_supported_format(name):
            cname = name.rsplit('.', 1)[0]
            cnames.setdefault(cname, []).append(name)
        else:
            cnames[name] = [name]
    return cnames


def diff_streams(p1, p2, verbose=False, ffmpeg_bin=None):
    if not audio_equal(p1, p2, ffmpeg_bin):
        print('Audio streams in {0} and {1} differ'.format(p1, p2))
        return 1
    elif verbose:
        print('Audio streams in {0} and {1} are identical'.format(p1, p2))
    return 0


def diff_tags(p1, p2, verbose=False, brief=False):
    if sys.stdout.isatty() and termcolor is not None:
        colored = termcolor.colored
        cprint = termcolor.cprint
    else:
        colored = lambda *options: options[0]
        cprint = print
    tags1 = tags(p1)
    tags2 = tags(p2)
    if tags1 == tags2:
        if verbose:
            print('Tags in {0} and {1} are identical'.format(p1, p2))
        return 0
    if brief:
        print('Tags in {0} and {1} differ'.format(p1, p2))
        return 1
    data = _compare_dicts(tags1, tags2)
    colors = {'-': 'red', '+': 'green', ' ': None}
    cprint(colored('--- {0}'.format(p1), colors['-']))
    cprint(colored('+++ {0}'.format(p2), colors['+']))
    for sign, key, value in data:
        if sign == ' ' and not verbose:
            continue
        value = str(value)
        if len(value) > 100:
            value = value[:92] + '...' + value[-5:]
        cprint(colored('{0}{1}: {2}'.format(sign, key, value), colors[sign]))
    return 1


def _compare_dicts(dict1, dict2):
    """
    Compares two dictionary-like objects and returns a list of tuples
    (*sign*, *key*, *value*). *sign* is '-' if the key is present
    in the first object but not in the second, or the key is present in
    both objects but the values differ. A '+' sign means the opposite.
    A ' ' sign means the key and value are present in both objects.

    Examples:

    >>> compare_dicts({'a': 1, 'b': 2, 'c': 3}, {'b': 2, 'c': 5, 'd': 7})
    [('-', 'a', 1), (' ', 'b', 2), ('-', 'c', 3), ('+', 'c', 5), ('+', 'd', 7)]

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


def diff_binary(p1, p2, verbose=False):
    if not equal(p1, p2):
        print('Files {0} and {1} differ'.format(p1, p2))
        return 1
    elif verbose:
        print('Files {0} and {1} are identical'.format(p1, p2))
    return 0
