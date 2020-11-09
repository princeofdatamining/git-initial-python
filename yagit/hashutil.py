# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods
""" hash """
import binascii
import hashlib
# from yagit import constant


_DIGEST_SIZE_TABLE = {}


def _cache_digest_size(hashobj):
    size = _DIGEST_SIZE_TABLE.get(hashobj.algorithm)
    if size:
        return size
    size = len(hashobj.calc(b""))
    return _DIGEST_SIZE_TABLE.setdefault(hashobj.algorithm, size)


class Hash:
    """ 哈希类 """

    def __init__(self, algorithm):
        self.algorithm = algorithm
        self.digest_size = _cache_digest_size(self)

    def calc(self, body):
        """ 计算哈希 """
        instance = hashlib.new(self.algorithm, body)
        return instance.digest()

    @staticmethod
    def hexdigest(digest):
        """ 十六进制输出 """
        return binascii.b2a_hex(digest).decode("utf8")


DEFAULT = SHA1 = Hash("sha1")
