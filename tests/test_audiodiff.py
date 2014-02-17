# -*- coding: utf-8 -*-
import os
import sys
from unicodedata import normalize

import pytest
parametrize = pytest.mark.parametrize

import audiodiff
from audiodiff import commandlinetool


@pytest.fixture(scope='session', autouse=True)
def setup(request):
    def teardown():
        os.chdir(old_cwd)
    old_cwd = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(__file__), 'files'))
    request.addfinalizer(teardown)


@parametrize(('name1', 'name2', 'truth'), [
    ('mahler.flac', 'mahler.m4a', True),
    ('mahler.flac', 'mahler_tagsdiff.m4a', False),
    ('mahler.flac', 'mahler.mp3', False),
    ('mahler.m4a', 'mahler_tagsdiff.m4a', False),
    ('mahler.m4a', 'mahler.mp3', False),
    ('mahler_tagsdiff.m4a', 'mahler.mp3', False),
])
def test_equal(name1, name2, truth):
    assert audiodiff.equal(name1, name2) == truth


@parametrize(('name1', 'name2', 'truth'), [
    ('mahler.flac', 'mahler.wav', True),
    ('mahler.flac', 'mahler.m4a', True),
    ('mahler.flac', 'mahler_tagsdiff.m4a', True),
    ('mahler.flac', 'mahler.mp3', False),
    ('mahler.m4a', 'mahler_tagsdiff.m4a', True),
    ('mahler.m4a', 'mahler.mp3', False),
    ('mahler_tagsdiff.m4a', 'mahler.mp3', False),
])
def test_audio_equal(name1, name2, truth):
    assert audiodiff.audio_equal(name1, name2) == truth


@parametrize(('name1', 'name2', 'truth'), [
    ('mahler.flac', 'mahler.wav', False),
    ('mahler.flac', 'mahler.m4a', True),
    ('mahler.flac', 'mahler_tagsdiff.m4a', False),
    ('mahler.flac', 'mahler.mp3', True),
    ('mahler.m4a', 'mahler_tagsdiff.m4a', False),
    ('mahler.m4a', 'mahler.mp3', True),
    ('mahler_tagsdiff.m4a', 'mahler.mp3', False),
])
def test_tags_equal(name1, name2, truth):
    assert audiodiff.tags_equal(name1, name2) == truth


@parametrize(('name', 'md5'), [
    ('mahler.wav', '9b2450efb790f0a00642b9f7d9526f08598a3d13'),
    ('mahler.flac', '9b2450efb790f0a00642b9f7d9526f08598a3d13'),
    ('mahler.m4a', '9b2450efb790f0a00642b9f7d9526f08598a3d13'),
    ('mahler_tagsdiff.m4a', '9b2450efb790f0a00642b9f7d9526f08598a3d13'),
    ('mahler.mp3', '000a49967e00b55f85f58e8859915b12e5a4121c'),
])
def test_checksum(name, md5):
    assert audiodiff.checksum(name) == md5


def test_checksum_error():
    with pytest.raises(audiodiff.ExternalLibraryError):
        audiodiff.checksum('x/foo.txt')


tags1 = {
    'album': 'Symphony No. 1 in D',
    'artist': 'Mahler',
    'composer': 'Claudio Abbado / Berlin Ph',
    'composersortorder': 'Abbado, Claudio / Berlin Ph',
    'date': '1888',
    'genre': 'A/Orchestral/Symphony',
    'title': 'III. Feierlich und gemessen, ohne zu schleppen',
    'tracknumber': '3',
    'tracktotal': '4',
}
tags2 = {
    'album': 'Symphony No. 1 in D',
    'artist': 'Mahler',
    'date': '1888',
    'genre': 'Orchestral/Symphony',
    'title': 'III',
    'tracknumber': '3',
    'tracktotal': '0',
    'x_foo': 'bar',
}


@parametrize(('name', 'tags'), [
    ('mahler.flac', tags1),
    ('mahler.m4a', tags1),
    ('mahler.mp3', tags1),
    ('mahler_tagsdiff.m4a', tags2),
])
def test_tags(name, tags):
    assert audiodiff.tags(name) == tags


def test_tags_error():
    with pytest.raises(audiodiff.UnsupportedFileError):
        audiodiff.tags('x/foo.txt')


@parametrize(('path', 'extension'), [
    ('a.pdf', 'pdf'),
    ('b.js.coffee', 'coffee'),
    ('c', ''),
    ('d/e.txt', 'txt'),
])
def test_get_extension(path, extension):
    assert audiodiff.get_extension(path) == extension


@parametrize(('name1', 'name2', 'out', 'err'), [
    ('mahler.flac', 'mahler.m4a', '', ''),
    ('mahler.flac', 'mahler.mp3', '', ''),
    ('mahler.flac', 'mahler_tagsdiff.m4a', """--- mahler.flac
+++ mahler_tagsdiff.m4a
-composer: Claudio Abbado / Berlin Ph
-composersortorder: Abbado, Claudio / Berlin Ph
-genre: A/Orchestral/Symphony
+genre: Orchestral/Symphony
-title: III. Feierlich und gemessen, ohne zu schleppen
+title: III
-tracktotal: 4
+tracktotal: 0
+x_foo: bar
""", ''),
])
def test_diff_tags(name1, name2, out, err, capsys):
    commandlinetool.diff_tags(name1, name2)
    assert capsys.readouterr() == (out, err)


def test_diff_tags_unicode(capsys):
    commandlinetool.diff_tags('mahler.flac', 'unicode.flac')
    out, err = capsys.readouterr()
    assert out == u"""--- mahler.flac
+++ unicode.flac
-title: III. Feierlich und gemessen, ohne zu schleppen
+title: II. Kräftig bewegt, doch nicht zu schnell
"""
    assert err == ''


@parametrize(('dict1', 'dict2', 'rv'), [
    ({}, {}, []),
    ({'a': 1}, {}, [('-', 'a', 1)]),
    ({}, {'a': 1}, [('+', 'a', 1)]),
    ({'a': 1, 'b': 2, 'c': 3},
     {'b': 2, 'c': 5, 'd': 7},
     [('-', 'a', 1), (' ', 'b', 2), ('-', 'c', 3), ('+', 'c', 5),
      ('+', 'd', 7)]),
])
def test_compare_dicts(dict1, dict2, rv):
    assert commandlinetool._compare_dicts(dict1, dict2) == rv


@parametrize(('args', 'return_code', 'out', 'err'), [
    (['mahler.flac', 'mahler.m4a'], 0, '', ''),
    (['mahler.flac', 'mahler.m4a', '-s'], 0,
     """Audio streams in mahler.flac and mahler.m4a are identical
Tags in mahler.flac and mahler.m4a are identical
""", ''),
    (['mahler.flac', 'mahler_tagsdiff.m4a', '-a'], 0, '', ''),
    (['mahler.flac', 'mahler_tagsdiff.m4a', '-t', '-q'], 1,
     """Tags in mahler.flac and mahler_tagsdiff.m4a differ
""", ''),
    (['mahler.flac', 'mahler.mp3', '--tags'], 0, '', ''),
    (['y', 'z'], 0, '', ''),
    (['x', 'y'], 1, normalize('NFC', u"""Files x/animal and y/animal differ
--- x/ä.flac
+++ y/ä.m4a
-composer: Claudio Abbado / Berlin Ph
-composersortorder: Abbado, Claudio / Berlin Ph
-genre: A/Orchestral/Symphony
+genre: Orchestral/Symphony
-title: III. Feierlich und gemessen, ohne zu schleppen
+title: III
-tracktotal: 4
+tracktotal: 0
+x_foo: bar
Only in x: b.txt
Audio streams in x/d.mp3 and y/d.flac differ
Only in x: hello
Only in y: world
"""), ''),
    (['x', 'y', '--brief'], 1,
     normalize('NFC', u"""Files x/animal and y/animal differ
Tags in x/ä.flac and y/ä.m4a differ
Only in x: b.txt
Audio streams in x/d.mp3 and y/d.flac differ
Only in x: hello
Only in y: world
"""), ''),
    (['x', 'y', '-s'], 1,
     normalize('NFC', u"""Files x/animal and y/animal differ
Audio streams in x/ä.flac and y/ä.m4a are identical
--- x/ä.flac
+++ y/ä.m4a
 album: Symphony No. 1 in D
 artist: Mahler
-composer: Claudio Abbado / Berlin Ph
-composersortorder: Abbado, Claudio / Berlin Ph
 date: 1888
-genre: A/Orchestral/Symphony
+genre: Orchestral/Symphony
-title: III. Feierlich und gemessen, ohne zu schleppen
+title: III
 tracknumber: 3
-tracktotal: 4
+tracktotal: 0
+x_foo: bar
Audio streams in x/b.m4a and y/b.flac are identical
Tags in x/b.m4a and y/b.flac are identical
Audio streams in x/b.m4a and y/b.m4a are identical
Tags in x/b.m4a and y/b.m4a are identical
Only in x: b.txt
Audio streams in x/c.flac and y/c.flac are identical
Tags in x/c.flac and y/c.flac are identical
Audio streams in x/c.flac and y/c.m4a are identical
Tags in x/c.flac and y/c.m4a are identical
Audio streams in x/c.m4a and y/c.flac are identical
Tags in x/c.m4a and y/c.flac are identical
Audio streams in x/c.m4a and y/c.m4a are identical
Tags in x/c.m4a and y/c.m4a are identical
Audio streams in x/d.mp3 and y/d.flac differ
Tags in x/d.mp3 and y/d.flac are identical
Files x/foo.txt and y/foo.txt are identical
Only in x: hello
Only in y: world
"""), ''),
    (['x', 'y', '--report-identical-files', '-q'], 1,
     normalize('NFC', u"""Files x/animal and y/animal differ
Audio streams in x/ä.flac and y/ä.m4a are identical
Tags in x/ä.flac and y/ä.m4a differ
Audio streams in x/b.m4a and y/b.flac are identical
Tags in x/b.m4a and y/b.flac are identical
Audio streams in x/b.m4a and y/b.m4a are identical
Tags in x/b.m4a and y/b.m4a are identical
Only in x: b.txt
Audio streams in x/c.flac and y/c.flac are identical
Tags in x/c.flac and y/c.flac are identical
Audio streams in x/c.flac and y/c.m4a are identical
Tags in x/c.flac and y/c.m4a are identical
Audio streams in x/c.m4a and y/c.flac are identical
Tags in x/c.m4a and y/c.flac are identical
Audio streams in x/c.m4a and y/c.m4a are identical
Tags in x/c.m4a and y/c.m4a are identical
Audio streams in x/d.mp3 and y/d.flac differ
Tags in x/d.mp3 and y/d.flac are identical
Files x/foo.txt and y/foo.txt are identical
Only in x: hello
Only in y: world
"""), ''),
    (['mahler.flac', 'x'], 2, '',
     """audiodiff: No such file or directory: 'x/mahler.flac'
"""),
    (['w', 'z'], 2, '', """audiodiff: No such file or directory: 'w'
"""),
])
def test_main_func(args, return_code, out, err, capsys):
    assert commandlinetool.main_func(args) == return_code
    actual = capsys.readouterr()
    assert normalize('NFC', actual[0]) == out
    assert normalize('NFC', actual[1]) == err
