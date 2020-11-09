# -*- coding: utf-8 -*-
""" constant """

CACHE_SIGNATURE = b"DIRC"
CACHE_VERSION = 2

OBJECTS = "objects"
CACHE = "index"

ZOBJ_BLOB = b"blob "
ZOBJ_TREE = b"tree "
ZOBJ_COMMIT = b"commit "
CHR_NUL = b"\x00"
NUM_NUL = 0

# 1 second = ? nanoseconds
NS_UNIT = 1000000000

# CacheEntry 中 hash 偏移
CE_HASH_OFFSET = 40

E_OBJ_DEC_HEADER = "invalid object header"
E_OBJ_DEC_BLOB_SIZE = "cannot read object size"
E_OBJ_DEC_SIZE = "dismatched size"
E_CACHE_ENTRY_NAME = "Missing NUL after path: {}"
E_CACHE_SIGNATURE = "Cant load CACHE_SIGNATURE"
E_CACHE_VERSION = "Cant load CACHE_VERSION"
E_CACHE_HASH = "Cache hash error: {}(read) != {}(calc)"


def combine_nanoseconds(seconds, nanoseconds):
    """ make (seconds, nanoseconds) """
    return seconds * NS_UNIT + nanoseconds
    # return seconds + float(remain) / constant.NS_UNIT


def parse_nanoseconds(value):
    """ get (seconds, nanoseconds) """
    seconds, remain = divmod(value, NS_UNIT)
    # seconds = int(value)
    # remain = int((value - seconds) * constant.NS_UNIT)
    return seconds, remain


def sizeof_cache_entry(namelen, digest_size):
    """ 优化大小，保证内存对齐
    /*
     * dev/ino/uid/gid/size are also just tracked to the low 32 bits
     * Again - this is just a (very strong in practice) heuristic that
     * the inode hasn't changed.
     */
    struct cache_entry {
        struct cache_time ctime;
        struct cache_time mtime;
        unsigned int st_dev;
        unsigned int st_ino;
        unsigned int st_mode;
        unsigned int st_uid;
        unsigned int st_gid;
        unsigned int st_size;
        unsigned char sha1[20];
        unsigned short namelen;
        unsigned char name[0];
    };
    """
    return (CE_HASH_OFFSET + digest_size + 2 + namelen + 8) & ~7


def sizeof_name(namelen, digest_size):
    """ name 实际分配内存大小 """
    ce_size = sizeof_cache_entry(namelen, digest_size)
    return ce_size - CE_HASH_OFFSET - digest_size - 2
