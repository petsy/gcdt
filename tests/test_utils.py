from nose.tools import with_setup, assert_equal

# http://stackoverflow.com/questions/6670275/python-imports-for-tests-using-nose-what-is-best-practice-for-imports-of-modul
# to install gcdt in dev mode use: "pip install -e ."
from StringIO import StringIO
from gcdt.utils import version, __version__


def bla():
    """test setup  clears the  dictionary."""
    pass
    # do something here...


@with_setup(bla)
def test_version():
    out = StringIO()
    version(out=out)
    assert_equal(out.getvalue().strip(), 'gcdt version %s' % __version__)


def test_retries():
    # TODO: add test when working on ramuda!
    pass