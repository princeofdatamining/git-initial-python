# -*- coding: utf-8 -*-
""" blob & zlib """
import io
import os
import zlib
from yagit import constant


class ObjectDecompressError(Exception):
    """ .git blob decompress """


class ObjectLoadError(Exception):
    """ Not Found .git/objects/hash[:2]/hash[2:] """


class ZGenericObject:
    """ .git/objects/hash[:2]/hash[2:] """

    HEADER = b""

    def __init__(self, fileobj, hashobj, raw):
        self.blob = None
        self.envelop = io.BytesIO()
        self.compressed = io.BytesIO()
        if raw:
            self.compress(fileobj)
        else:
            self.decompress(fileobj)
        self.hxid = hashobj.calc(self.envelop.getbuffer())

    def compress(self, fileobj):
        """ zlib compress """
        if hasattr(fileobj, "read"):
            blob = fileobj.read()
        else:
            blob = fileobj
        #
        self.envelop.truncate(0)
        self.envelop.seek(0, 0)
        self.envelop.write(self.HEADER)
        self.envelop.write(str(len(blob)).encode("utf8"))
        self.envelop.write(constant.CHR_NUL)
        offset = self.envelop.tell()
        self.envelop.write(blob)
        #
        self.blob = self.envelop.getbuffer()[offset:]
        #
        self.compressed.truncate(0)
        self.compressed.seek(0, 0)
        self.compressed.write(zlib.compress(
            self.envelop.getbuffer(),
            zlib.Z_BEST_SPEED))

    def decompress(self, fileobj):
        """ zlib decompress """
        self.compressed.truncate(0)
        self.compressed.seek(0, 0)
        if hasattr(fileobj, "read"):
            self.compressed.write(fileobj.read())
        else:
            self.compressed.write(fileobj)
        #
        self.envelop.truncate(0)
        self.envelop.seek(0, 0)
        self.envelop.write(zlib.decompress(self.compressed.getbuffer()))
        buffer = self.envelop.getvalue()
        #
        capacity = len(buffer)
        # 1+sprintf(metadata, "blob %lu", (unsigned long) st->st_size)
        if not self.HEADER or not buffer.startswith(self.HEADER):
            raise ObjectDecompressError(constant.E_OBJ_DEC_HEADER)
        offset = fixed = len(self.HEADER)
        while offset < min(capacity, 32): # unsigned long maximum length?
            # "offset != 5": at least one digit
            # "buffer[offset] == NUL": end when met NUL
            if offset != fixed and buffer[offset] == constant.NUM_NUL:
                break
            # digits: '0'..'9'
            if not 0x30 <= buffer[offset] <= 0x39:
                raise ObjectDecompressError(constant.E_OBJ_DEC_BLOB_SIZE)
            offset += 1
        else:
            raise ObjectDecompressError(constant.E_OBJ_DEC_BLOB_SIZE)
        size = int(buffer[fixed:offset])
        offset += 1
        if offset + size != capacity:
            raise ObjectDecompressError(constant.E_OBJ_DEC_SIZE)
        self.blob = self.envelop.getbuffer()[offset:]

    @staticmethod
    def load_compressed(fileobj, hashobj):
        """ guess type """
        # read zlib binary
        buf = fileobj.read(64)
        fileobj.seek(-len(buf), 1)
        # try decompress
        decompressobj = zlib.decompressobj()
        header = decompressobj.decompress(buf)
        # parse it
        for klass in ZOBJECT_CLASS_LIST:
            if header.startswith(klass.HEADER):
                return klass(fileobj, hashobj, raw=False)
        raise ObjectDecompressError(constant.E_OBJ_DEC_HEADER)


class ZBlobObject(ZGenericObject):
    """ blob object """

    HEADER = constant.ZOBJ_BLOB


class ZTreeObject(ZGenericObject):
    """ tree object """

    HEADER = constant.ZOBJ_TREE


class ZCommitObject(ZGenericObject):
    """ commit object """

    HEADER = constant.ZOBJ_COMMIT


ZOBJECT_CLASS_LIST = [ZBlobObject, ZTreeObject, ZCommitObject]


# pylint: disable=too-few-public-methods
class ZStream:
    """ ZStream """

    def __init__(self, fout, zclass, hashobj):
        self.fout = fout
        self.zclass = zclass
        self.hashobj = hashobj
        self.zobj = None

    def write(self, data):
        """ 生成 ZGenericObject 并存储 """
        self.zobj = self.zclass(data, self.hashobj, raw=True)
        self.fout.write(self.zobj.compressed.getvalue())


class ZObjects:
    """ .git/objects """

    def __init__(self, hashobj, objects_dir):
        self.hashobj = hashobj
        self.objects_dir = objects_dir
        self.objects = {}

    def _get_key(self, hash_or_zobj):
        if isinstance(hash_or_zobj, ZGenericObject):
            return self.hashobj.hexdigest(hash_or_zobj.hxid)
        if isinstance(hash_or_zobj, str):
            return hash_or_zobj
        return self.hashobj.hexdigest(hash_or_zobj)

    def get(self, hash_or_zobj):
        """ 读取 """
        key = self._get_key(hash_or_zobj)
        cache = self.objects.get(key)
        if not cache:
            return self.load(key)
        return cache

    def set(self, zobj):
        """ 存入 """
        key = self._get_key(zobj)
        if key not in self.objects:
            self.save(key, zobj)
            self.objects[key] = zobj
        return zobj

    def add(self, fileobj, header_or_class):
        """ 创建并存入 """
        for klass in ZOBJECT_CLASS_LIST:
            if header_or_class in (klass, klass.HEADER):
                return self.set(klass(fileobj, self.hashobj, raw=True))
        raise ObjectDecompressError(constant.E_OBJ_DEC_HEADER)

    def get_filename(self, key):
        """ 文件名 """
        headname, basename = key[:2], key[2:]
        #
        dirname = os.path.join(self.objects_dir, headname)
        if not os.path.exists(dirname):
            os.mkdir(dirname, 0o700)
        #
        return os.path.join(dirname, basename)

    def load(self, key):
        """ 从磁盘加载 """
        if not self.objects_dir:
            raise ObjectLoadError()
        filename = self.get_filename(key)
        with open(filename, "rb") as fin:
            return self.set(ZGenericObject.load_compressed(fin, self.hashobj))

    def save(self, key, zobj):
        """ 存储到磁盘 """
        if not self.objects_dir:
            return
        filename = self.get_filename(key)
        if os.path.exists(filename):
            return
        with open(filename, "wb") as fout:
            fout.write(zobj.compressed.getbuffer())

    ########
    # misc #
    ########

    def create_zstream(self, klass):
        """ 创建 ZStream """
        stream = io.BytesIO()
        return ZStream(stream, klass, self.hashobj)

    def create_tree(self):
        """ 创建 ZStream(Tree) """
        return self.create_zstream(ZTreeObject)

    def create_commit(self, message, ztree):
        """ 创建 ZStream(Commit) """
        body = message.format(self.hashobj.hexdigest(ztree.hxid))
        zcommit = ZCommitObject(body.encode("utf8"), self.hashobj, raw=True)
        self.set(zcommit)
        return zcommit
