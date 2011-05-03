""" Testing prundles
"""

from os.path import (join as pjoin, sep as filesep)

from ..prundle import (PathPrundle, ZipPrundle, PrundleError,
                       make_prundle, common_zip_path)

from nose.tools import assert_true, assert_equal, assert_raises

from ..testing import DANG_DATA_PATH


def test_make_prundle():
    # Test factory function for prundles
    http_dang_path = 'file://' + DANG_DATA_PATH.replace(filesep, '/')
    for fsp_path in (pjoin(DANG_DATA_PATH, 'eg-pkg'),
                     pjoin(DANG_DATA_PATH, 'eg-pkg.zip'),
                     http_dang_path + '/eg-pkg',
                    ):
        fsprd = make_prundle(fsp_path)
        # The metadata comes from the read package:
        assert_equal(fsprd.pinstant.pkg_name, 'example-package')
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
    # path objects have base_path attribute
    fsp_path = pjoin(DANG_DATA_PATH, 'eg-pkg')
    fsprd = make_prundle(fsp_path)
    assert_equal(fsprd.base_path, fsp_path)
    # A read or passed package name - is necessary:
    no_meta_path = pjoin(DANG_DATA_PATH, 'no-meta')
    assert_raises(PrundleError, make_prundle, no_meta_path)


def test_common_path():
    # test common path routine
    assert_equal(common_zip_path(['here/now', 'here/', 'here/hey/there']),
                 'here/')
    assert_equal(common_zip_path(['hey/now', 'here/', 'here/hey/there']),
                 None)
    # Must begin with slash
    assert_equal(common_zip_path(['here/now', 'here/', 'herehey/there']),
                 None)
    assert_equal(common_zip_path(['here/now']), 'here/')
