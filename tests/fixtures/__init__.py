import pytest

from ..context import audiodiff


DIFFZIP_PARAMS = [
    ([], [], []),
    (['a'], [], [('a', None)]),
    (['a', 'b'], ['a'], [('a', 'a'), ('b', None)]),
    (['a', 'b'], ['a', 'a', 'b'], [('a', 'a'), (None, 'a'), ('b', 'b')]),
    (['a', 'c', 'd'],
     ['b', 'd', 'e'],
     [('a', None), (None, 'b'), ('c', None), ('d', 'd'), (None, 'e')]),
]
PATH_PARAMS = [
    ('test.flac', 'test'),
    ('foo/bar.m4a', 'foo/bar'),
    ('something.jpg', 'something.jpg'),
]


@pytest.fixture(params=range(len(DIFFZIP_PARAMS)))
def diffzip_params(request):
    return DIFFZIP_PARAMS[request.param]


@pytest.fixture(params=range(len(PATH_PARAMS)))
def path_params(request):
    return PATH_PARAMS[request.param]
