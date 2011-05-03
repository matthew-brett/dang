""" Package instantiation provider bundle
"""

from os.path import (split as psplit, join as pjoin, sep as filesep,
                     isdir, isfile)
import re
import urllib2
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
    root_maker = lambda x : x

    def __init__(self, pinstant, root):
        self.pinstant = pinstant
        self.root = root

    @classmethod
    def uri_to_root(klass, uri):
        """ Class method to return file-provider from `uri'

        Parameters
        ----------
        uri : str

        Returns
        -------
        root : file-provider
            implments open(sub-path) method
        """
        return klass.root_maker(uri,
                                klass.default_binary_mode,
                                klass.default_text_mode)

    def get_fileobj(self, sub_path, mode=None):
        """ Return open fileobj from prundle
        """
        if mode is None:
            mode = self.default_binary_mode
        return self.root.open(sub_path, mode)

    @classmethod
    def from_path(klass, path, pkg_name=None, meta=None):
        return klass.from_root(klass.uri_to_root(path), pkg_name, meta)

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
        cfg_name, cfg_meta = klass.root_to_config(root)
        if pkg_name is None:
            if cfg_name is None:
                raise PrundleError('No read or passed package name')
            pkg_name = cfg_name
        elif pkg_name != cfg_name:
            raise PrundleError('Read package name "%s" differs from passed '
                               'package name "%s"' % (cfg_name,
                                                      pkg_name))
        if meta is None:
            meta = {}
        # Fill passed meta with read meta key, value pairs
        for key, value in cfg_meta.items():
            if not key in meta:
                meta[key] = value
            else: # keys in both, check they are the same
                if meta[key] != value:
                    raise PrundleError('Read meta value for %s is %s and '
                                       'differs from passed meta value %s' %
                                       (key, value, meta[key]))
        return klass(Pinstant(pkg_name, meta), root)

    @classmethod
    def root_to_config(klass, root):
        config = ConfigParser.SafeConfigParser()
        try:
            cfg_file = root.open('meta.ini', klass.default_text_mode)
        except IOError:
            pass
        else:
            config.readfp(cfg_file)
            cfg_file.close()
        meta = dict(config.items('DEFAULT'))
        pkg_name = meta.pop('pkg_name', None)
        return pkg_name, meta


def common_zip_path(file_list):
    """ Return root directory common to all zip file paths

    Parameters
    ----------
    file_list : sequence
        list of files in zip archive

    Returns
    -------
    common_path : str
        shortest string at the start of all entries in `file_list` that ends
        with a ``/``.  None if there is no such component
    """
    components0 = file_list[0].split('/', 1)
    if len(components0) == 1:
        return None
    to_test = components0[0] + '/'
    for e in file_list[1:]:
        if not e.startswith(to_test):
            return None
    return to_test


class ZipRoot(object):
    def __init__(self,
                 path,
                 default_binary_mode='r',
                 default_text_mode='rU'):
        self.zipobj = zipfile.ZipFile(path)
        self.common_path = common_zip_path(self.zipobj.namelist())
        self.default_binary_mode = default_binary_mode
        self.default_text_mode = default_text_mode

    def open(self, sub_path, mode=None):
        if mode is None:
            mode = self.default_binary_mode
        if not self.common_path is None:
            sub_path = self.common_path + sub_path
        return self.zipobj.open(sub_path, mode)


class ZipPrundle(FSPrundle):
    default_binary_mode = 'r'
    default_text_mode = 'rU'
    root_maker = ZipRoot


class PathRoot(object):
    def __init__(self,
                 base_path,
                 default_binary_mode='rb',
                 default_text_mode='rU'):
        self.base_path = base_path
        self.default_binary_mode = default_binary_mode
        self.default_text_mode = default_text_mode

    def open(self, sub_path, mode=None):
        if mode is None:
            mode = self.default_binary_mode
        if filesep != "/":
            sub_path = sub_path.replace('/', filesep)
        return open(pjoin(self.base_path, sub_path), mode=mode)


class PathPrundle(FSPrundle):
    root_maker = PathRoot

    def __init__(self, pinstant, root):
        self.pinstant = pinstant
        self.root = root
        self.base_path = self.root.base_path


class UrlRoot(object):
    def __init__(self,
                 base_url,
                 default_binary_mode=None,
                 default_text_mode=None):
        self.base_url = base_url

    def open(self, sub_path, mode=None):
        if not mode is None:
            if not 'r' in mode or 't' in mode:
                raise ValueError('No flexible modes for urls')
        return urllib2.urlopen(self.base_url + '/' + sub_path)


class UrlPathPrundle(FSPrundle):
    default_binary_mode = 'r'
    default_text_mode = 'r'
    root_maker = UrlRoot

    def __init__(self, pinstant, root):
        self.pinstant = pinstant
        self.root = root
        self.base_url = self.root.base_url


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
    >>> fsprd.base_path == fsp_path
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
        return UrlPathPrundle.from_path(uri, pkg_name, meta)
    # Assume it's a filename
    pth, ext = psplit(uri)
    if ext in ('tar', '.tar', '.tgz', '.bz2'):
        PrundleError("Can't deal with this right now")
    if uri.endswith('.zip'):
        return ZipPrundle.from_path(uri, pkg_name, meta)
    if not isdir(uri):
        PrundleError('I thought you were going to give me a directory')
    return PathPrundle.from_path(uri, pkg_name, meta)

