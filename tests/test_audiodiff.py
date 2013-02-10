from .context import audiodiff
from .fixtures import diffzip_params, path_params


def test_diffzip(diffzip_params):
    lst1, lst2, rv = diffzip_params
    assert audiodiff.diffzip(lst1, lst2) == rv


class TestPath:

    def test_hideext(self, path_params):
        path, rv = path_params
        p = audiodiff.Path(path)
        p.hideext()
        assert str(p) == rv
