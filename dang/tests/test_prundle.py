""" Testing prundles
"""

from os.path import (split as psplit, join as pjoin, sep as filesep,
                     isdir, isfile)

from ..prundle import (PathPrundle, ZipPrundle, PrundleError,
                       make_prundle)

from nose.tools import assert_true, assert_equal, assert_raises

from ..testing import DANG_DATA_PATH


def test_make_prundle():
    # Test factory function for prundles
    for pkg_spath in ('eg-pkg',
                      'eg-pkg.zip'):
        fsp_path = pjoin(DANG_DATA_PATH, pkg_spath)
        fsprd = make_prundle(fsp_path)
        # The metadata comes from the read package:
        assert_equal(fsprd.pinstant.pkg_name, 'example-package')
        assert_equal(fsprd.root, fsp_path)
        # If the read metadata conflicts with the passed metadata, generate an error:
        assert_raises(PrundleError, make_prundle, fsp_path, 'another_name')
        # Here the package name is the same, so it works
        fsprd = make_prundle(fsp_path, 'example-package')
        # Other metadata differs
        assert_raises(PrundleError, make_prundle, fsp_path, 'example-package',
                    {'unusual_key': 'interesting data'})
        # This works because the metadata is the same
        fsprd = make_prundle(fsp_path, 'example-package',
                            {'unusual_key': 'nonsense data'})
        # We can get fileobjs
        readf = fsprd.get_fileobj('README')
        assert_equal(readf.readlines(), ['This is a README\n', '\n'])
    # A read or passed package name - is necessary:
    no_meta_path = pjoin(DANG_DATA_PATH, 'no-meta')
    assert_raises(PrundleError, make_prundle, no_meta_path)
