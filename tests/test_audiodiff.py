import pytest

from .context import audiodiff


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
    assert audiodiff.diffzip(list1, list2) == rv


@pytest.mark.parametrize(('path', 'path_without_ext'), [
    ('test.flac', 'test'),
    ('foo/bar.m4a', 'foo/bar'),
    ('something.jpg', 'something.jpg'),
])
def test_path(path, path_without_ext):
    p = audiodiff.Path(path)
    p.hideext()
    assert str(p) == path_without_ext
