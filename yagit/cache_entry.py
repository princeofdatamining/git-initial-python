# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods
""" cache entry """
import io
import stat
from collections import namedtuple
from yagit import constant
from yagit import pathutil
from yagit import byteutil


class CacheEntryLoadError(Exception):
    """ Load CacheEntry """


CacheStat = namedtuple("CacheStat", [
    "st_mode", "st_ino", "st_dev", "st_nlink",
    "st_uid", "st_gid", "st_size",
    "st_atime_ns", "st_mtime_ns", "st_ctime_ns"])


def read_stat(reader):
    """ Read CacheStat from reader """
    st_ctime_ns = reader.read_ns() # 0:8
    st_mtime_ns = reader.read_ns() # 8:16
    st_dev = reader.read_uint() # 16:20
    st_ino = reader.read_uint() # 20:24
    st_mode = reader.read_uint() # 24:28
    st_uid = reader.read_uint() # 28:32
    st_gid = reader.read_uint() # 32:36
    st_size = reader.read_uint() # 36:40
    return CacheStat(
        st_mode,
        st_ino,
        st_dev,
        0,
        st_uid,
        st_gid,
        st_size,
        st_mtime_ns,
        st_mtime_ns,
        st_ctime_ns)


def parse_mode(mode):
    """ stat.st_mode: (int, oct) """
    if isinstance(mode, int):
        return mode, oct(mode)[2:]
    return int(mode, 8), mode


def is_tree_mode(mode):
    """ 0o040000 S_IFDIR # directory """
    return parse_mode(mode)[0] == stat.S_IFDIR


class GenericEntry:
    """ generic entry """

    # pylint: disable=no-member
    def compare(self, path_or_name):
        """ 比较(用于排序) """
        if isinstance(path_or_name, str):
            value = self.path
        else:
            value = self.name
        if value == path_or_name:
            return 0
        if value < path_or_name:
            return -1
        return 1


class CacheEntry(GenericEntry):
    """ cache entry """

    # pylint: disable=too-many-arguments
    def __init__(self, path, fstat, zobj, order, stream=None):
        self.path = path
        self.name = pathutil.encode_path(path)
        self.stat = fstat
        self.zobj = zobj
        self.order = order
        self.stream = stream or io.BytesIO()
        self.helper = byteutil.ByteOrderStream(order, self.stream)
        if self.stream != stream:
            self.flush()

    def flush(self):
        """ 写入 """
        self.stream.truncate(0)
        self.stream.seek(0, 0)
        self.helper.write_ns(self.stat.st_ctime_ns) # 0:8
        self.helper.write_ns(self.stat.st_mtime_ns) # 8:16
        self.helper.write_uint(self.stat.st_dev) # 16:20
        self.helper.write_uint(self.stat.st_ino) # 20:24
        self.helper.write_uint(self.stat.st_mode & ~stat.S_IWGRP) # 24:28
        self.helper.write_uint(self.stat.st_uid) # 28:32
        self.helper.write_uint(self.stat.st_gid) # 32:36
        self.helper.write_uint(self.stat.st_size) # 36:40
        self.stream.write(self.zobj.hxid) # 40:60
        self.helper.write_ushort(len(self.name)) # 60:62
        self.stream.write(self.name)
        padding = pathutil.padding_path(len(self.name), len(self.zobj.hxid))
        self.stream.write(padding)

    @classmethod
    def parse_one(cls, helper, objects):
        """ 读取 """
        writer = io.BytesIO()
        tee = byteutil.TeeStream(fin=helper.stream, fout=writer)
        helper = byteutil.ByteOrderStream(helper.order, tee)
        #
        fstat = read_stat(helper)
        #
        hxid = helper.stream.read(objects.hashobj.digest_size)
        zobj = objects.get(hxid)
        #
        pathlen = helper.read_ushort()
        path = pathutil.decode_path(helper.stream.read(pathlen))
        padding = pathutil.padding_path(pathlen, objects.hashobj.digest_size)
        if helper.stream.read(len(padding)) != padding:
            raise CacheEntryLoadError(constant.E_CACHE_ENTRY_NAME.format(path))
        return cls(path, fstat, zobj, helper.order, stream=writer)


class TreeEntry(GenericEntry):
    """ tree entry """

    def __init__(self, path, mode, zobj):
        self.path = path
        self.name = pathutil.encode_path(path)
        self.mode_int, self.mode_hex = parse_mode(mode)
        self.zobj = zobj
        self.stream = io.BytesIO()
        # Is still a tree?
        self.tree = None
        self.flush()

    def is_tree(self):
        """ 0o040000 S_IFDIR # directory """
        return self.mode_int == stat.S_IFDIR

    def flush(self):
        """ 写入 """
        if self.zobj is None:
            return
        self.stream.truncate(0)
        self.stream.seek(0, 0)
        self.stream.write(self.mode_hex.encode("utf8"))
        self.stream.write(b" ")
        self.stream.write(self.name)
        self.stream.write(constant.CHR_NUL)
        self.stream.write(self.zobj.hxid)
