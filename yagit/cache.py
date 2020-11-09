# -*- coding: utf-8 -*-
""" cache """
import os
import io
import stat
from yagit import constant
# from yagit import pathutil
from yagit import byteutil
from yagit import cache_entry


class CacheLoadError(Exception):
    """ .git/index loader """


class AbstractTree:
    """ AbstractTree """

    def __init__(self, objects):
        self.objects = objects
        self.entries = []
        self.stream = io.BytesIO()
        self.order = byteutil.Network
        self.helper = byteutil.ByteOrderStream(self.order, self.stream)

    def add_entry(self, entry):
        """ 添加 entry """
        pos = self.find(entry.path)
        # existing match? Just replace it
        if pos < 0:
            pos = -pos-1
            self.entries[pos] = entry
        else:
            self.entries.insert(pos, entry)
        return pos, entry

    def find(self, path_or_name):
        """ 定位
        - 存在返回负值(如果存在并且索引为0，为与插入区分，需要转换为负值)
        - 插入返回非负值
        """
        first, last = 0, len(self.entries) - 1
        while first <= last:
            middle = (first + last) >> 1
            ret = self.entries[middle].compare(path_or_name)
            if ret == 0:
                return -middle-1
            if ret < 0:
                first = middle + 1
            else:
                last = middle - 1
        return first

    def remove_file(self, path):
        """ 移除 """
        pos = self.find(path)
        if pos < 0:
            self.entries.pop(-pos-1)

    def _write_header(self):
        pass

    def _write_eof(self):
        pass

    def _write_to(self, fout):
        fout.write(self.stream.getvalue())

    def flush(self, fout=None):
        """ 落盘 """
        self.stream.truncate(0)
        self.stream.seek(0, 0)
        # header
        self._write_header()
        # entries
        for entry in self.entries:
            self.stream.write(entry.stream.getbuffer())
        # eof
        self._write_eof()
        #
        if fout is not None:
            self._write_to(fout)


class Cache(AbstractTree):
    """ Cache """

    def add(self, path):
        """ 添加 file """
        if not os.path.exists(path):
            self.remove_file(path)
            return
        with open(path, "rb") as fin:
            zobj = self.objects.add(fin, constant.ZOBJ_BLOB)
        fstat = os.stat(path)
        entry = cache_entry.CacheEntry(path, fstat, zobj, self.order)
        self.add_entry(entry)

    def _write_header(self):
        # header
        self.stream.write(constant.CACHE_SIGNATURE)
        self.helper.write_uint(constant.CACHE_VERSION)
        self.helper.write_uint(len(self.entries))

    def _write_eof(self):
        # hash
        self.stream.write(self.objects.hashobj.calc(self.stream.getbuffer()))

    def load(self, fin):
        """ 读取 """
        self.entries.clear()
        self.stream.truncate(0)
        self.stream.seek(0, 0)
        # read then write
        tee = byteutil.TeeStream(fin=fin, fout=self.stream)
        helper = byteutil.ByteOrderStream(self.order, tee)
        # header
        if tee.read(4) != constant.CACHE_SIGNATURE:
            raise CacheLoadError(constant.E_CACHE_SIGNATURE)
        if helper.read_uint() != constant.CACHE_VERSION:
            raise CacheLoadError(constant.E_CACHE_VERSION)
        entries = helper.read_uint()
        # entries
        for _ in range(entries):
            entry = cache_entry.CacheEntry.parse_one(helper, self.objects)
            self.add_entry(entry)
        # hash
        calced = self.objects.hashobj.calc(self.stream.getvalue())
        loaded = tee.read()
        if calced != loaded:
            raise CacheLoadError(constant.E_CACHE_HASH.format(
                self.objects.hashobj.hexdigest(loaded),
                self.objects.hashobj.hexdigest(calced)))
        #


class Tree(AbstractTree):
    """ Tree """

    def __init__(self, objects, parent=None, path=""):
        self.parent = parent
        self.path = path
        self.zobj = None
        super().__init__(objects)

    def add(self, path, mode, hxid):
        """ 添加 file """
        dirname, _, basename = path.partition('/')
        # 1. 如果直接添加 DIR 仅可能来自 load 无需建立子树
        # 2. 添加带目录的 FILE 需要建立子树，而且子树的 hash 要最终 flush 才能确定
        if basename and not cache_entry.is_tree_mode(mode):
            subtree = self.lookup_subtree(dirname, do_insert=True)
            return subtree.add(basename, mode, hxid)
        entry = cache_entry.TreeEntry(path, mode, self.objects.get(hxid))
        return self.add_entry(entry)

    def lookup_subtree(self, dirname, do_insert):
        """ 子树 """
        for entry in self.entries:
            if entry.is_tree() and entry.path == dirname:
                return entry.tree
        # Not found
        if not do_insert:
            return None
        # Create!
        entry = cache_entry.TreeEntry(dirname, stat.S_IFDIR, None)
        entry.tree = Tree(self.objects, parent=self, path=dirname)
        self.add_entry(entry)
        return entry.tree

    def load(self, zobj):
        """ 读取 """
        self.zobj = zobj
        self.entries.clear()
        body = zobj.blob.tobytes()
        pos = 0
        while pos < len(body):
            # read mode
            off_space = body[pos:].index(b" ")
            mode = body[pos:pos+off_space].decode("utf8")
            off_space += 1
            pos += off_space
            # read path
            off_nul = body[pos:].index(constant.CHR_NUL)
            path = body[pos:pos+off_nul].decode("utf8")
            off_nul += 1
            pos += off_nul
            # read hash
            off_hxid = self.objects.hashobj.digest_size
            digest = body[pos:pos+off_hxid]
            # hxid = self.objects.hashobj.hexdigest(digest)
            pos += off_hxid
            #
            _, entry = self.add(path, mode, digest)
            if entry.is_tree():
                entry.tree = Tree(self.objects, parent=self, path=path)
                entry.tree.load(entry.zobj)
            #

    def _write_to(self, fout):
        super()._write_to(fout)
        # 存储 tree object
        self.objects.set(fout.zobj)

    def walk(self, ancestor=None):
        """ 遍历 """
        if ancestor is None:
            ancestor = [self]
        for entry in self.entries:
            if not entry.is_tree():
                yield (entry, ancestor)
            else:
                for item in entry.tree.walk(ancestor + [entry.tree]):
                    yield item

    def flush(self, fout=None):
        """ 落盘(递归) """
        for entry in self.entries:
            if entry.is_tree() and entry.zobj is None:
                entry.tree.flush()
                entry.zobj = entry.tree.zobj
                entry.flush()
        #
        ztree_stream = self.objects.create_tree()
        if fout is not None:
            super().flush(byteutil.CloneWriter(ztree_stream, fout))
        else:
            super().flush(ztree_stream)
        self.zobj = ztree_stream.zobj
