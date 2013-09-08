import os
__dir__ = os.path.dirname(__file__)
import sys
sys.path.insert(0, os.path.join(__dir__, '..'))

import pytest
import audiodiff


def fx(filename):
    return os.path.join(__dir__, 'fixtures', filename)


def test_checksum():
    assert audiodiff.checksum(fx('mahler.flac')) == 'db5ef0d702f66ce8b6a27395c32e1d28'
    assert audiodiff.checksum(fx('mahler.m4a')) == 'db5ef0d702f66ce8b6a27395c32e1d28'
    assert audiodiff.checksum(fx('mahler_tagsdiff.m4a')) == 'db5ef0d702f66ce8b6a27395c32e1d28'
    assert audiodiff.checksum(fx('mahler.mp3')) == 'cc9b70f5a71d1849e85f13ba7dda0322'


def test_audioequal():
    assert audiodiff.audioequal(fx('mahler.flac'), fx('mahler.m4a'))
    assert audiodiff.audioequal(fx('mahler.flac'), fx('mahler_tagsdiff.m4a'))
    assert not audiodiff.audioequal(fx('mahler.flac'), fx('mahler.mp3'))
    assert audiodiff.audioequal(fx('mahler.m4a'), fx('mahler_tagsdiff.m4a'))
    assert not audiodiff.audioequal(fx('mahler.m4a'), fx('mahler.mp3'))
    assert not audiodiff.audioequal(fx('mahler_tagsdiff.m4a'), fx('mahler.mp3'))


def test_tagsequal():
    assert audiodiff.tagsequal(fx('mahler.flac'), fx('mahler.m4a'))
    assert not audiodiff.tagsequal(fx('mahler.flac'), fx('mahler_tagsdiff.m4a'))
    assert audiodiff.tagsequal(fx('mahler.flac'), fx('mahler.mp3'))
    assert not audiodiff.tagsequal(fx('mahler.m4a'), fx('mahler_tagsdiff.m4a'))
    assert audiodiff.tagsequal(fx('mahler.m4a'), fx('mahler.mp3'))
    assert not audiodiff.tagsequal(fx('mahler_tagsdiff.m4a'), fx('mahler.mp3'))


def test_equal():
    assert audiodiff.equal(fx('mahler.flac'), fx('mahler.m4a'))
    assert not audiodiff.equal(fx('mahler.flac'), fx('mahler_tagsdiff.m4a'))
    assert not audiodiff.equal(fx('mahler.flac'), fx('mahler.mp3'))
    assert not audiodiff.equal(fx('mahler.m4a'), fx('mahler_tagsdiff.m4a'))
    assert not audiodiff.equal(fx('mahler.m4a'), fx('mahler.mp3'))
    assert not audiodiff.equal(fx('mahler_tagsdiff.m4a'), fx('mahler.mp3'))


def test_tags():
    tags = {
      'album': 'Symphony No. 1 in D',
      'artist': 'Mahler',
      'composer': 'Claudio Abbado / Berlin Ph',
      'composersortorder': 'Abbado, Claudio / Berlin Ph',
      'date': '1888',
      'genre': 'A/Orchestral/Symphony',
      'title': 'III. Feierlich und gemessen, ohne zu schleppen',
      'tracknumber': '3',
      'tracktotal': '4'
    }
    assert audiodiff.tags(fx('mahler.flac')) == tags
    assert audiodiff.tags(fx('mahler.m4a')) == tags
    assert audiodiff.tags(fx('mahler.mp3')) == tags
    assert audiodiff.tags(fx('mahler_tagsdiff.m4a')) == {
      'album': 'Symphony No. 1 in D',
      'artist': 'Mahler',
      'date': '1888',
      'genre': 'Orchestral/Symphony',
      'title': 'III',
      'tracknumber': '3',
      'tracktotal': '0',
      'x_foo': 'bar'
    }


def test_tagsdiff(capsys):
    audiodiff.tagsdiff(fx('mahler.flac'), fx('mahler.m4a'))
    assert capsys.readouterr()[0] == ''
    audiodiff.tagsdiff(fx('mahler.flac'), fx('mahler.mp3'))
    assert capsys.readouterr()[0] == ''
    audiodiff.tagsdiff(fx('mahler.flac'), fx('mahler_tagsdiff.m4a'))
    assert capsys.readouterr()[0] == """--- {0}
+++ {1}
-composer: Claudio Abbado / Berlin Ph
-composersortorder: Abbado, Claudio / Berlin Ph
-genre: A/Orchestral/Symphony
+genre: Orchestral/Symphony
-title: III. Feierlich und gemessen, ohne zu schleppen
+title: III
-tracktotal: 4
+tracktotal: 0
+x_foo: bar
""".format(fx('mahler.flac'), fx('mahler_tagsdiff.m4a'))


@pytest.mark.parametrize(('dict1', 'dict2', 'rv'), [
    ({}, {}, (True, [])),
    ({'a': 1}, {}, (False, [('-', 'a', 1)])),
    ({}, {'a': 1}, (False, [('+', 'a', 1)])),
    ({'a': 1, 'b': 2, 'c': 3},
     {'b': 2, 'c': 5, 'd': 7},
     (False, [('-', 'a', 1),
              (' ', 'b', 2),
              ('-', 'c', 3),
              ('+', 'c', 5),
              ('+', 'd', 7)])),
])
def test_dictcmp(dict1, dict2, rv):
    assert audiodiff.dictcmp(dict1, dict2) == rv


@pytest.mark.parametrize(('list1', 'list2', 'rv'), [
    ([], [], []),
    (['a'], [], [('a', None)]),
    (['a', 'b'], ['a'], [('a', 'a'), ('b', None)]),
    (['a', 'b'], ['a', 'a', 'b'], [('a', 'a'), (None, 'a'), ('b', 'b')]),
    (['a', 'c', 'd'],
     ['b', 'd', 'e'],
     [('a', None), (None, 'b'), ('c', None), ('d', 'd'), (None, 'e')]),
])
def test_diffzip(list1, list2, rv):
    assert audiodiff._diffzip(list1, list2) == rv


@pytest.mark.parametrize(('path', 'path_without_ext'), [
    ('test.flac', 'test'),
    ('foo/bar.m4a', 'foo/bar'),
    ('something.jpg', 'something.jpg'),
])
def test_path(path, path_without_ext):
    p = audiodiff._Path(path)
    p.hideext()
    assert str(p) == path_without_ext
