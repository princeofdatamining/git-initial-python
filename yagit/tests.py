# -*- coding: utf-8 -*-
# pylint: disable=missing-function-docstring
""" test yagit """
import io
import os
import binascii
from unittest import TestCase
from yagit import constant
# from yagit import pathutil
# from yagit import byteutil # constant
from yagit import hashutil # constant
from yagit import blobutil # <hashobj>
from yagit import cache_entry # pathutil, byteutil
from yagit import cache # pathutil, byteutil, cache_entry, <objects>


# 0o100644 <==> 0b1,000,000,110,100,100 <==> 0b1000,0001,1010,0100 <==> 0x81a4
# 0o100664 <==> 0b1,000,000,110,110,100 <==> 0b1000,0001,1011,0100 <==> 0x81b4
#---------
# 0o140000 S_IFSOCK# socket
# 0o120000 S_IFLNK # symbolic link
# 0o100000 S_IFREG # regular file
# 0o060000 S_IFBLK # block device
# 0o040000 S_IFDIR # directory
# 0o020000 S_IFCHR # character device
# 0o010000 S_IFIFO # FIFO
#
# 0o000400 S_IRUSR # owner has read permission
# 0o000200 S_IWUSR # owner has write permission
# 0o000100 S_IXUSR # owner has execute permission
#
# 0o000040 S_IRGRP # group has read permission
# 0o000020 S_IWGRP # group has write permission
# 0o000010 S_IXGRP # group has execute permission
#
# 0o000004 S_IROTH # others have read permission
# 0o000002 S_IWOTH # others have write permission
# 0o000001 S_IXOTH # others have execute permission

def _hexload(inputs):
    hexstr = "".join(inputs).replace(" ", "").encode("utf8")
    return binascii.a2b_hex(hexstr)


# $ cat hello.txt
HELLO_TXT = """hello, world.

"""

# $ git add hello.txt
# $ hexdump -C .git/objects/d2/7a234c4c241d1bab7e87db50baa8ffb4274d8c
HELLO_ZLIB = _hexload([
    "78 01 4b ca c9 4f 52 30  34 65 c8 48 cd c9 c9 d7",#  |x.K..OR04e.H....|
    "51 28 cf 2f ca 49 d1 e3  e2 02 00 57 cf 06 f0",#     |Q(./.I.....W...|
])
# b'blob 15\x00hello, world.\n\n'

HELLO_STAT = (
    "d27a234c4c241d1bab7e87db50baa8ffb4274d8c", "hello.txt",
    # mode, ino, dev, nlink, uid=1010(0x03f2), gid=1011(0x03f3), size=0x0f
    0o100644, 0x1552ac5f, 0xfd00, 0, 1010, 1011, 15,
    constant.combine_nanoseconds(0x5fa01c62, 0x12d62201)) # 1604328546, 316023297

# $ hexdump -C .git/index
INDEX_1ST = _hexload([
    "44 49 52 43 00 00 00 02  00 00 00 01 5f a0 1c 62",#  |DIRC........_..b|
    "12 d6 22 01 5f a0 1c 62  12 d6 22 01 00 00 fd 00",#  |.."._..b..".....|
    "15 52 ac 5f 00 00 81 a4  00 00 03 f2 00 00 03 f3",#  |.R._............|
    "00 00 00 0f d2 7a 23 4c  4c 24 1d 1b ab 7e 87 db",#  |.....z#LL$...~..|
    "50 ba a8 ff b4 27 4d 8c  00 09 68 65 6c 6c 6f 2e",#  |P....'M...hello.|
    "74 78 74 00 fd 67 f6 a5  1f 4e 60 1f 4d 7e 13 a4",#  |txt..g...N`.M~..|
    "f4 61 09 84 c0 7e 87 72",#                           |.a...~.r|
])

# $ git commit -m "..."
# $ hexdump -C .git/objects/ec/7d6a20ce7e445941760fa7dba2a2bcefc75d79
TREE_1_SHA1 = "ec7d6a20ce7e445941760fa7dba2a2bcefc75d79"
TREE_1_ZLIB = _hexload([
    "78 01 2b 29 4a 4d 55 30  36 67 30 34 30 30 33 31",#  |x.+)JMU06g040031|
    "51 c8 48 cd c9 c9 d7 2b  a9 28 61 b8 54 a5 ec e3",#  |Q.H....+.(a.T...|
    "a3 22 2b bd ba ae fd 76  c0 ae 15 ff b7 a8 fb f6",#  |."+....v........|
    "00 00 44 34 10 7f",#                                 |..D4..|
])
# b"tree 37\x00
#100644 hello.txt\x00<d27a234c4c241d1bab7e87db50baa8ffb4274d8c>
#"

# $ hexdump -C .git/objects/0c/68231c6718993a47bf9245d3c411e9d514f871
COMMIT_1_SHA1 = "0c68231c6718993a47bf9245d3c411e9d514f871"
COMMIT_1_ZLIB = _hexload([
    "78 01 95 8d 41 0a c2 30  10 45 5d e7 14 b3 17 ca",#  |x...A..0.E].....|
    "34 a6 9d 46 44 c4 2b 78  82 69 32 a1 42 62 24 8e",#  |4..FD.+x.i2.Bb$.|
    "d0 e3 9b 2b b8 fd ef 3d  7e a8 a5 3c 15 46 9a 0f",#  |...+...=~..<.F..|
    "da 44 40 02 c5 99 2d 06  21 71 6e f2 ae 13 4c 4c",#  |.D@...-.!qn...LL|
    "71 65 cb 76 0d 92 02 4d  91 bc e1 af 6e b5 c1 83",#  |qe.v...M....n...|
    "5f 70 af 2b 5c 0a 7f 54  da 4d 76 2e ef 2c 43 a8",#  |_p.+\..T.Mv..,C.|
    "e5 0a e3 8c ce e3 69 71  04 47 5c 10 4d 5f fb 5b",#  |......iq.G\.M_.[|
    "f7 fe ec 4c 12 d6 33 70  8c b0 49 ce 75 d0 5d cd",#  |...L..3p..I.u.].|
    "0f 2c f8 39 2d",#                                    |.,.9-|
])
# b'commit 176\x00<ec7d6a20ce7e445941760fa7dba2a2bcefc75d79>'

COMMIT_1 = """tree {}
author San Bob <master@example.com> 1604903847 +0800
committer San Bob <master@example.com> 1604903847 +0800

feat: add hello.txt
"""

################################################################################

ZERO_TXT = ""

# $ hexdump -C .git/objects/e6/9de29bb2d1d6434b8b29ae775ad8c2e48c5391
ZERO_ZLIB = _hexload([
    "78 01 4b ca c9 4f 52 30  60 00 00 09 b0 01 f0",   #  |x.K..OR0`......|
])
# b'blob 0\x00'

INIT_PY = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

# $ hexdump -C .git/objects/78/477809e8322dffd8ef77c374131620fd887c2e
INIT_ZLIB = _hexload([
    "78 01 4b ca c9 4f 52 30  b1 60 50 56 d4 2f 2d 2e",#  |x.K..OR0.`PV./-.|
    "d2 4f ca cc d3 4f cd 2b  53 28 a8 2c c9 c8 cf 33",#  |.O...O.+S(.,...3|
    "e6 52 56 d0 d5 d2 55 48  ce 4f c9 cc 4b b7 52 28",#  |.RV...UH.O..K.R(|
    "2d 49 d3 b5 00 89 70 71  01 00 e1 e9 0f f9",#        |-I....pq......|
])
# b'blob 48\x00...'

ABC_README_STAT = (
    "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391", "abc/README.md",
    0o100644, 0x0a0dee4f, 0xfd00, 0, 1010, 1011, 0,
    constant.combine_nanoseconds(0x5fa4eeda, 0x1e3db611))

ABC_HELLO_STAT = (
    "d27a234c4c241d1bab7e87db50baa8ffb4274d8c", "abc/欢迎.txt",
    0o100644, 0x0a0dee50, 0xfd00, 0, 1010, 1011, 15,
    constant.combine_nanoseconds(0x5fa4eef8, 0x08818a34))

XYZ_README_STAT = (
    "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391", "xyz/README-读我.md",
    0o100644, 0x0b0ae0fc, 0xfd00, 0, 1010, 1011, 0,
    constant.combine_nanoseconds(0x5fa4eeda, 0x1e3db611))

XYZ_INIT_STAT = (
    "78477809e8322dffd8ef77c374131620fd887c2e", "xyz/__init__.py",
    0o100644, 0x0b0ae0fe, 0xfd00, 0, 1010, 1011, 48,
    constant.combine_nanoseconds(0x5fa4ef45, 0x104ef11f))

# $ git add abc/* xyz/*
# $ hexdump -C .git/index
INDEX_2ND = _hexload([
    "44 49 52 43 00 00 00 02  00 00 00 05 5f a4 ee da",#  |DIRC........_...|
    "1e 3d b6 11 5f a4 ee da  1e 3d b6 11 00 00 fd 00",#  |.=.._....=......|
    "0a 0d ee 4f 00 00 81 a4  00 00 03 f2 00 00 03 f3",#  |...O............|
    "00 00 00 00 e6 9d e2 9b  b2 d1 d6 43 4b 8b 29 ae",#  |...........CK.).|
    "77 5a d8 c2 e4 8c 53 91  00 0d 61 62 63 2f 52 45",#  |wZ....S...abc/RE|
    "41 44 4d 45 2e 6d 64 00  00 00 00 00 5f a4 ee f8",#  |ADME.md....._...|
    "08 81 8a 34 5f a4 ee f8  08 81 8a 34 00 00 fd 00",#  |...4_......4....|
    "0a 0d ee 50 00 00 81 a4  00 00 03 f2 00 00 03 f3",#  |...P............|
    "00 00 00 0f d2 7a 23 4c  4c 24 1d 1b ab 7e 87 db",#  |.....z#LL$...~..|
    "50 ba a8 ff b4 27 4d 8c  00 0e 61 62 63 2f e6 ac",#  |P....'M...abc/..|
    "a2 e8 bf 8e 2e 74 78 74  00 00 00 00 5f a0 1c 62",#  |.....txt...._..b|
    "12 d6 22 01 5f a0 1c 62  12 d6 22 01 00 00 fd 00",#  |.."._..b..".....|
    "15 52 ac 5f 00 00 81 a4  00 00 03 f2 00 00 03 f3",#  |.R._............|
    "00 00 00 0f d2 7a 23 4c  4c 24 1d 1b ab 7e 87 db",#  |.....z#LL$...~..|
    "50 ba a8 ff b4 27 4d 8c  00 09 68 65 6c 6c 6f 2e",#  |P....'M...hello.|
    "74 78 74 00 5f a4 ee da  1e 3d b6 11 5f a4 ee da",#  |txt._....=.._...|
    "1e 3d b6 11 00 00 fd 00  0b 0a e0 fc 00 00 81 a4",#  |.=..............|
    "00 00 03 f2 00 00 03 f3  00 00 00 00 e6 9d e2 9b",#  |................|
    "b2 d1 d6 43 4b 8b 29 ae  77 5a d8 c2 e4 8c 53 91",#  |...CK.).wZ....S.|
    "00 14 78 79 7a 2f 52 45  41 44 4d 45 2d e8 af bb",#  |..xyz/README-...|
    "e6 88 91 2e 6d 64 00 00  00 00 00 00 5f a4 ef 45",#  |....md......_..E|
    "10 4e f1 1f 5f a4 ef 45  10 4e f1 1f 00 00 fd 00",#  |.N.._..E.N......|
    "0b 0a e0 fe 00 00 81 a4  00 00 03 f2 00 00 03 f3",#  |................|
    "00 00 00 30 78 47 78 09  e8 32 2d ff d8 ef 77 c3",#  |...0xGx..2-...w.|
    "74 13 16 20 fd 88 7c 2e  00 0f 78 79 7a 2f 5f 5f",#  |t.. ..|...xyz/__|
    "69 6e 69 74 5f 5f 2e 70  79 00 00 00 93 1c 7c 72",#  |init__.py.....|r|
    "5d 94 6a 19 89 39 00 c2  4e 87 7c e8 dd d7 9f 1b",#  |].j..9..N.|.....|
])

# $ git commit -m "..."
# $ hexdump -C .git/objects/26/48b02921964c4e2e19395f69c831b09e2ebcde
TREE_2_SHA1 = "2648b02921964c4e2e19395f69c831b09e2ebcde"
TREE_2_ZLIB = _hexload([
    "78 01 2b 29 4a 4d 55 b0  34 67 30 31 00 02 85 c4",#  |x.+)JMU.4g01....|
    "a4 64 86 52 41 c3 19 1c  af 7e 85 4d 99 e6 9a a8",#  |.d.RA....~.M....|
    "38 b3 57 42 61 8a 8f b2  a1 81 81 99 89 89 42 46",#  |8.WBa.........BF|
    "6a 4e 4e be 5e 49 45 09  c3 a5 2a 65 1f 1f 15 59",#  |jNN.^IE...*e...Y|
    "e9 d5 75 ed b7 03 76 ad  f8 bf 45 dd b7 07 62 44",#  |..u...v...E...bD|
    "45 65 15 c3 4d a1 74 db  73 f9 9c b6 73 1d 0c a2",#  |Ee..M.t.s...s...|
    "df 7c ba 64 97 b1 40 b5  0d 00 48 ca 26 3c",#        |.|.d..@...H.&<|
])
# b"tree 97\x00
#40000  abc\x00      <7511319808eafa569496456121998d1820944c23>
#100644 hello.txt\x00<d27a234c4c241d1bab7e87db50baa8ffb4274d8c>
#40000  xyz\x00      <d912673dce6f093d9d40305becf2d23e68a02586>"

# $ hexdump -C .git/objects/75/11319808eafa569496456121998d1820944c23
TREE_ABC_SHA1 = "7511319808eafa569496456121998d1820944c23"
TREE_ABC_ZLIB = _hexload([
    "78 01 2b 29 4a 4d 55 30  37 65 30 34 30 30 33 31",#  |x.+)JMU07e040031|
    "51 08 72 75 74 f1 75 d5  cb 4d 61 78 36 f7 d1 ec",#  |Q.rut.u..Max6...|
    "4d 17 af 39 7b 77 6b ae  2b 8f ba 71 e8 49 4f f0",#  |M..9{wk.+..q.IO.|
    "44 a8 a2 67 6b 16 bd d8  df a7 57 52 51 c2 70 a9",#  |D..gk.....WRQ.p.|
    "4a d9 c7 47 45 56 7a 75  5d fb ed 80 5d 2b fe 6f",#  |J..GEVzu]...]+.o|
    "51 f7 ed 01 00 36 75 22  da",#                       |Q....6u".|
])
# b"tree 75\x00
#100644 README.md\x00                   <e69de29bb2d1d6434b8b29ae775ad8c2e48c5391>
#100644 \xe6\xac\xa2\xe8\xbf\x8e.txt\x00<d27a234c4c241d1bab7e87db50baa8ffb4274d8c>"

# $ hexdump -C .git/objects/d9/12673dce6f093d9d40305becf2d23e68a02586
TREE_XYZ_SHA1 = "d912673dce6f093d9d40305becf2d23e68a02586"
TREE_XYZ_ZLIB = _hexload([
    "78 01 2b 29 4a 4d 55 b0  30 66 30 34 30 30 33 31",#  |x.+)JMU.0f040031|
    "51 08 72 75 74 f1 75 d5  7d b1 7e f7 b3 8e 89 7a",#  |Q.rut.u.}.~....z|
    "b9 29 0c cf e6 3e 9a bd  e9 e2 35 67 ef 6e cd 75",#  |.)...>....5g.n.u|
    "e5 51 37 0e 3d e9 09 9e  08 55 1b 1f 9f 99 97 59",#  |.Q7.=....U.....Y|
    "12 1f af 57 50 c9 50 e1  5e c1 f9 c2 48 f7 ff 8d",#  |...WP.P.^...H...|
    "f7 e5 87 4b 84 c5 14 fe  76 d4 e8 01 00 76 1c 25",#  |...K....v....v.%|
    "c7",#                                                |.|
])
# b'tree 83\x00
#100644 README-\xe8\xaf\xbb\xe6\x88\x91.md\x00  <e69de29bb2d1d6434b8b29ae775ad8c2e48c5391>
#100644 __init__.py\x00                         <78477809e8322dffd8ef77c374131620fd887c2e>'

# $ hexdump -C .git/objects/c0/51902c02e4d397703d8d3d610758ef87db0ca5
COMMIT_2_SHA1 = "c051902c02e4d397703d8d3d610758ef87db0ca5"
COMMIT_2_ZLIB = _hexload([
    "78 01 95 ce 5d 0a 42 21  10 86 e1 ae 5d c5 dc 07",#  |x...].B!....]...|
    "e1 f8 77 9c 88 88 b6 d0  0a 46 9d 43 41 1e c3 0c",#  |..w......F.CA...|
    "5a 7e 6e a1 db 87 f7 83  2f b7 5a 1f 03 0c d2 6e",#  |Z~n...../.Z....n|
    "74 11 30 c1 c5 a4 0d 4d  08 2e 3b 31 82 64 c9 af",#  |t.0....M..;1.d..|
    "81 72 b4 98 34 4d 49 b9  88 7a 71 97 6d 80 ce 21",#  |.r..4MI..zq.m..!|
    "1a 8b 39 2c 18 89 2c bb  25 ad 64 9c 2f 36 3b 44",#  |..9,..,.%.d./6;D|
    "a1 e2 d1 ad 71 41 c5 9f  71 6f 1d 6e bc c1 b5 25",#  |....qA..qo.n...%|
    "38 55 7e 0f e9 17 f9 72  7d 3d e5 90 5b 3d 03 06",#  |8U~....r}=..[=..|
    "ed 88 62 44 0f 7b 1d b5  56 53 e7 bb d9 fd b9 53",#  |..bD.{..VS.....S|
    "ab f0 38 02 97 02 b5 75  51 3f e3 5f 42 fa",#        |..8....uQ?._B.|
])
# b'commit 219\x00<2648b02921964c4e2e19395f69c831b09e2ebcde>'

COMMIT_2 = """tree {}
parent 0c68231c6718993a47bf9245d3c411e9d514f871
author San Bob <master@example.com> 1604998815 +0800
committer San Bob <master@example.com> 1604998815 +0800

feat: add more
"""


def _new_entry(stat, objects, index):
    hxid = stat[0]
    path = stat[1]
    return cache_entry.CacheEntry(
        path,
        cache_entry.CacheStat(*stat[2:], stat[-1], stat[-1]),
        objects.get(hxid),
        index.order)


def _new_objects(files=(), trees=(), commits=()):
    objects = blobutil.ZObjects(hashutil.SHA1, None)
    for (klass, items) in [
            (blobutil.ZBlobObject, files),
            (blobutil.ZTreeObject, trees),
            (blobutil.ZCommitObject, commits),
    ]:
        for item in items:
            objects.set(klass(item, hashutil.SHA1, False))
    return objects


class GitTestCase(TestCase):
    """ test yagit
    """

    def setUp(self):
        files = (HELLO_ZLIB, ZERO_ZLIB, INIT_ZLIB,)
        trees = (TREE_ABC_ZLIB, TREE_XYZ_ZLIB, TREE_1_ZLIB, TREE_2_ZLIB,)
        commits = ()
        self.objects = _new_objects(files, trees, commits)

    def test_size(self):
        for (name_len, entry_size) in [
                (13, 80), (14, 80), (9, 72), (20, 88), (15, 80)]:
            calc = constant.sizeof_cache_entry(name_len, hashutil.SHA1.digest_size)
            self.assertEqual(entry_size, calc)

    def _test_hash(self, origin, blobized, digest):
        zobj = blobutil.ZBlobObject(origin, hashutil.SHA1, raw=True)
        self.assertEqual(zobj.compressed.getvalue(), blobized)
        self.assertEqual(
            hashutil.SHA1.hexdigest(zobj.hxid),
            digest.replace("/", ""))
        #
        zobj = blobutil.ZBlobObject(blobized, hashutil.SHA1, raw=False)
        self.assertEqual(zobj.blob.tobytes(), origin)
        self.assertEqual(
            hashutil.SHA1.hexdigest(zobj.hxid),
            digest.replace("/", ""))

    def test_object(self):
        self._test_hash(
            HELLO_TXT.encode("utf8"),
            HELLO_ZLIB,
            "d2/7a234c4c241d1bab7e87db50baa8ffb4274d8c")
        self._test_hash(
            ZERO_TXT.encode("utf8"),
            ZERO_ZLIB,
            "e6/9de29bb2d1d6434b8b29ae775ad8c2e48c5391")
        self._test_hash(
            INIT_PY.encode("utf8"),
            INIT_ZLIB,
            "78/477809e8322dffd8ef77c374131620fd887c2e")

    def test_simple_cache(self):
        # Load Cache
        objects = _new_objects(files=(HELLO_ZLIB,))
        index = cache.Cache(objects)
        stream = io.BytesIO(INDEX_1ST)
        index.load(stream)
        # Save Cache
        index = cache.Cache(objects)
        index.add_entry(_new_entry(HELLO_STAT, objects, index))
        index.flush()
        self.assertEqual(index.stream.getvalue(), INDEX_1ST[:index.stream.tell()])
        #

    def test_complex_cache(self):
        # Load Cache
        objects = _new_objects(files=(HELLO_ZLIB, ZERO_ZLIB, INIT_ZLIB,))
        index = cache.Cache(objects)
        stream = io.BytesIO(INDEX_2ND)
        index.load(stream)
        # Save Cache
        index = cache.Cache(objects)
        index.add_entry(_new_entry(XYZ_README_STAT, objects, index))
        index.add_entry(_new_entry(ABC_README_STAT, objects, index))
        index.add_entry(_new_entry(HELLO_STAT, objects, index))
        index.add_entry(_new_entry(ABC_HELLO_STAT, objects, index))
        index.add_entry(_new_entry(XYZ_INIT_STAT, objects, index))
        index.flush()
        self.assertEqual(index.stream.getvalue(), INDEX_2ND[:index.stream.tell()])
        #

    def test_simple_tree(self):
        # Save Tree
        objects = _new_objects(files=(HELLO_ZLIB, ZERO_ZLIB, INIT_ZLIB,))
        tree = cache.Tree(objects)
        tree.add_entry(cache_entry.TreeEntry(
            HELLO_STAT[1],
            HELLO_STAT[2],
            objects.get(HELLO_STAT[0])))
        tree.flush()
        self.assertEqual(tree.zobj.compressed.getvalue(), TREE_1_ZLIB)
        zcommit = objects.create_commit(COMMIT_1, tree.zobj)
        self.assertEqual(hashutil.SHA1.hexdigest(zcommit.hxid), COMMIT_1_SHA1)
        self.assertEqual(zcommit.compressed.getvalue(), COMMIT_1_ZLIB)
        # Load Tree
        ztree = blobutil.ZTreeObject(TREE_1_ZLIB, hashutil.SHA1, False)
        tree = cache.Tree(objects)
        tree.load(ztree)
        entry = tree.entries[0]
        self.assertEqual(hashutil.SHA1.hexdigest(entry.zobj.hxid), HELLO_STAT[0])
        self.assertEqual(entry.path, HELLO_STAT[1])
        self.assertEqual(entry.mode_int, HELLO_STAT[2])

    def test_complex_tree(self):
        # Save Tree
        objects = _new_objects(files=(HELLO_ZLIB, ZERO_ZLIB, INIT_ZLIB,))
        tree = cache.Tree(objects)
        tree.add(HELLO_STAT[1], HELLO_STAT[2], HELLO_STAT[0])
        tree.add(ABC_README_STAT[1], ABC_README_STAT[2], ABC_README_STAT[0])
        tree.add(ABC_HELLO_STAT[1], ABC_HELLO_STAT[2], ABC_HELLO_STAT[0])
        tree.add(XYZ_README_STAT[1], XYZ_README_STAT[2], XYZ_README_STAT[0])
        tree.add(XYZ_INIT_STAT[1], XYZ_INIT_STAT[2], XYZ_INIT_STAT[0])
        tree.flush()
        self.assertEqual(tree.zobj.compressed.getvalue(), TREE_2_ZLIB)
        zcommit = objects.create_commit(COMMIT_2, tree.zobj)
        self.assertEqual(hashutil.SHA1.hexdigest(zcommit.hxid), COMMIT_2_SHA1)
        self.assertEqual(zcommit.compressed.getvalue(), COMMIT_2_ZLIB)
        # Load Tree
        objects = _new_objects(
            files=(HELLO_ZLIB, ZERO_ZLIB, INIT_ZLIB,),
            trees=(TREE_2_ZLIB, TREE_ABC_ZLIB, TREE_XYZ_ZLIB))
        tree = cache.Tree(objects)
        tree.load(objects.get(TREE_2_SHA1))
        # check trees & files
        files = {
            ABC_README_STAT[1]: ABC_README_STAT[0],
            ABC_HELLO_STAT[1]: ABC_HELLO_STAT[0],
            HELLO_STAT[1]: HELLO_STAT[0],
            XYZ_README_STAT[1]: XYZ_README_STAT[0],
            XYZ_INIT_STAT[1]: XYZ_INIT_STAT[0],
        }
        for entry, ancestor in tree.walk():
            hxid = hashutil.SHA1.hexdigest(entry.zobj.hxid)
            path = os.path.join(*[e.path for e in ancestor], entry.path)
            self.assertEqual(hxid, files.pop(path, None))
        for hxid, path in files.items():
            self.assertIsNone((hxid, path))
        #
