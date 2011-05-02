""" Package instantiation provider bundle
"""

from os.path import (split as psplit, join as pjoin, sep as filesep,
                     isdir, isfile)
import re
import ConfigParser
import zipfile

class DangError(Exception):
    pass


class PrundleError(DangError):
    pass


class Pinstant(object):
    def __init__(self,
                 pkg_name,
                 meta):
        self.pkg_name = pkg_name
        self.meta = {}
        self.meta.update(meta)


class Prundle(object):
    """ Abstract base class
    """
    def __init__(self, pinstant):
        self.pinstant = pinstant


class FSPrundle(object):
    """ Prundle with a file-providing `root` object.

    A prundle wrapping a path would be one example, a zipfile would be
    another.

    A FSPrundle uses a 'meta.ini' file or file-like for its metadata.
    """
    default_binary_mode = 'rb'
    default_text_mode = 'rU'

    def __init__(self, pinstant, root):
        self.pinstant = pinstant
        self.root = root

    @classmethod
    def croot_get_fileobj(klass, root, sub_path, mode=None):
        """ Class method to return open fileobj from prundle
        """
        raise NotImplementedError

    def get_fileobj(self, sub_path, mode=None):
        """ Return open fileobj from prundle
        """
        return self.__class__.croot_get_fileobj(
            self.root,
            sub_path,
            self.default_binary_mode)

    @classmethod
    def from_root(klass, root, pkg_name=None, meta=None):
        """ Read prundle from file-providing `root`

        Parameters
        ----------
        root : object
            object that the class can get fileobjs from, using its class method.
        pkg_name : None or str
            name of package.  If None, defer to pkg_name as read from data in
            `root`.  If pkg_name as read from data in `root` conflicts with this
            one, raise PrundleError.
        meta : None or mapping, optional
            metadata.  If we find metadata at `root` we check `meta` for
            consistency with the found metadata, and raise a PrundleError if the
            metadata do not match

        Returns
        -------
        fsprd : klass instance
            instance of this `klass`
        """
        read_name, read_meta = klass._read_cfg(root)
        if pkg_name is None:
            if read_name is None:
                raise PrundleError('No read or passed package name')
            pkg_name = read_name
        elif pkg_name != read_name:
            raise PrundleError('Read package name "%s" differs from passed '
                               'package name "%s"' % (read_name,
                                                      pkg_name))
        if meta is None:
            meta = {}
        # Fill passed meta with read meta key, value pairs
        for key, value in read_meta.items():
            if not key in meta:
                meta[key] = value
            else: # keys in both, check they are the same
                if meta[key] != value:
                    raise PrundleError('Read meta value for %s is %s and '
                                       'differs from passed meta value %s' %
                                       (key, value, meta[key]))
        return klass(Pinstant(pkg_name, meta), root)

    @classmethod
    def _read_cfg(klass, root):
        config = ConfigParser.SafeConfigParser()
        try:
            cfg_file = klass.croot_get_fileobj(root,
                                               'meta.ini',
                                               klass.default_text_mode)
        except IOError:
            pass
        else:
            config.readfp(cfg_file)
            cfg_file.close()
        meta = dict(config.items('DEFAULT'))
        pkg_name = meta.pop('pkg_name', None)
        return pkg_name, meta


class ZipPrundle(FSPrundle):
    default_binary_mode = 'r'
    default_text_mode = 'rU'

    @classmethod
    def croot_get_fileobj(klass, root, sub_path, mode=None):
        """ Class method to return open fileobj from prundle
        """
        if mode is None:
            mode = klass.default_binary_mode
        return root.open(sub_path, mode)


class PathPrundle(FSPrundle):
    @classmethod
    def croot_get_fileobj(klass, root, sub_path, mode=None):
        """ Class method to return open fileobj from prundle
        """
        if mode is None:
            mode = klass.default_binary_mode
        if filesep != "/":
            sub_path = sub_path.replace('/', filesep)
        return open(pjoin(root, sub_path), mode=mode)


URI_REG = re.compile(r'(http|file|ftp)://(.*)')


def make_prundle(uri, pkg_name=None, meta=None):
    """ Create prundle from address `uri`

    Parameters
    ----------
    uri : str
        address of data from which to make prundle.
    pkg_name : None or str, optional
        name of package within prundle.  We'll read the prundle to get a name;
        if the read name conflicts with `pkg_name` we raise an error.
    meta : None or dict, optional
        metadata for package instantiation.  We read the prundle for metadata
        too.  `meta` should match the read metadata.

    Returns
    -------
    prd : prundle instance

    Examples
    --------
    >>> import os
    >>> from dang.testing import DANG_DATA_PATH
    >>> fsp_path = os.path.join(DANG_DATA_PATH, 'eg-pkg')
    >>> fsprd = make_prundle(fsp_path)

    The metadata comes from the read package:

    >>> fsprd.pinstant.pkg_name
    'example-package'
    >>> fsprd.root == fsp_path
    True

    If the read metadata conflicts with the passed metadata, generate an error:

    >>> fsprd = make_prundle(fsp_path, pkg_name='another_name')
    Traceback (most recent call last):
        ...
    PrundleError: Read package name "example-package" differs from passed package name "another_name"

    A read or passed package name - is necessary:

    >>> fsp_path = os.path.join(DANG_DATA_PATH, 'no-meta')
    >>> fsprd = make_prundle(fsp_path)
    Traceback (most recent call last):
        ...
    PrundleError: No read or passed package name
    """
    uri_match = URI_REG.match(uri)
    if not uri_match is None:
        PrundleError("Can't deal with this right now")
    pth, ext = psplit(uri)
    if ext in ('tar', '.tar', '.gz', '.bz2'):
        PrundleError("Can't deal with this right now")
    if uri.endswith('.zip'):
        root = zipfile.ZipFile(uri)
        return ZipPrundle.from_root(root, pkg_name, meta)
    if not isdir(uri):
        PrundleError('I thought you were going to give me a directory')
    return PathPrundle.from_root(uri, pkg_name, meta)

