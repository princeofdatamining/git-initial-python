# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods
""" database(.git) """
import os
from yagit import constant
from yagit import hashutil
from yagit import blobutil
from yagit import cache


class Database:
    """ .git Database """

    def __init__(self, workdir):
        self.workdir = workdir
        self.objects_dir = os.path.join(workdir, constant.OBJECTS)
        self.cache_file = os.path.join(workdir, constant.CACHE)
        #
        self.hashobj = hashutil.SHA1
        self.objects = blobutil.ZObjects(self.hashobj, self.objects_dir)
        #
        self.index = cache.Cache(self.objects)

    def _read_cache(self):
        if not os.path.exists(self.cache_file):
            return
        with open(self.cache_file, "rb") as fin:
            self.index.load(fin)

    def _proc_cache(self, func, *argv, flush=None):
        self._read_cache()
        func(*argv)
        if not flush:
            return
        with open(self.cache_file, "wb") as fout:
            fout.seek(0, 0)
            self.index.flush(fout)

    def _add_cache(self, *argv):
        for path in argv:
            self.index.add(path)

    def add(self, *argv):
        """ add <FILE>... """
        self._proc_cache(self._add_cache, *argv, flush=True)

    def cat(self, *argv):
        """ cat <SHA>... """
        for hxid in argv:
            hxid = hxid.replace("/", "")
            zobj = self.objects.get(hxid)
            print("##### {} #####".format(hxid))
            print(zobj.blob.tobytes())
            print("")

    def _commit_cache(self, message):
        tree = cache.Tree(self.objects)
        for entry in self.index.entries:
            tree.add(entry.path, entry.stat.st_mode, entry.zobj.hxid)
        tree.flush()
        #
        with open(message, "r", encoding="utf8") as fin:
            content = fin.read()
        _ = self.objects.create_commit(content, tree.zobj)
        #

    def commit(self, message):
        """ commit <MSG_FILE> """
        self._proc_cache(self._commit_cache, message, flush=None)

    def init(self):
        """ 初始化 .git 数据库 """
        if os.path.isdir(self.objects_dir):
            return
        if os.path.exists(self.objects_dir):
            print("bad directory %s." % self.objects_dir)
            return
        os.makedirs(self.objects_dir, 0o700, exist_ok=True)
        # print("unable to create %s." % self.objects_dir)
        print("defaulting to private storage area")
        # for i in range(256):
        #     path = "{}/{:02x}".format(self.objects_dir, i)
        #     os.mkdir(path, 0o700)
        #

    def _rm_cache(self, *argv):
        for path in argv:
            self.index.remove_file(path)

    # pylint: disable=invalid-name
    def rm(self, *argv):
        """ rm <FILE>... """
        self._proc_cache(self._rm_cache, *argv, flush=True)

    def _status_cache(self, *argv):
        for entry in self.index.entries:
            if not argv or entry.path in argv:
                print(entry.path, entry.stat.st_size, self.hashobj.hexdigest(entry.zobj.hxid))

    def status(self, *argv):
        """ status <FILE>... """
        self._proc_cache(self._status_cache, *argv, flush=None)
