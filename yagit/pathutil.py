# -*- coding: utf-8 -*-
""" path & file """
from yagit import constant


def verify_path(path):
    """ We fundamentally don't like some paths: we don't want
        dot or dot-dot anywhere, and in fact, we don't even want
        any other dot-files (.dircache or anything else). They
        are hidden, for chist sake.

        Also, we don't want double slashes or slashes at the
        end that can make pathnames ambiguous.
    """
    for part in path.split('/'):
        if not part or part.startswith('.'):
            return False
    return True


def encode_path(path):
    """ 默认存储编码为 utf8 """
    return path.encode("utf8")


def decode_path(path):
    """ 默认存储编码为 utf8 """
    return path.decode("utf8")


def padding_path(namelen, digest_size):
    """ 在 name 后补零 """
    reallen = constant.sizeof_name(namelen, digest_size)
    return bytes([0] * (reallen - namelen))
