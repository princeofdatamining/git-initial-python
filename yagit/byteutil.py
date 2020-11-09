# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods
""" big & little endian """
import struct
from yagit import constant


class ByteOrder:
    """ struct Byte Order

    See python struct docs - 7.1.2.1. Byte Order, Size, and Alignment
    """

    def __init__(self, order):
        self.order = order

    def write_uint(self, value):
        """ uint """
        return struct.pack(self.order + "I", value)

    def write_ushort(self, value):
        """ ushort """
        return struct.pack(self.order + "H", value)

    def read_uint(self, value):
        """ uint """
        gets = struct.unpack(self.order + "I", value)
        return gets[0]

    def read_ushort(self, value):
        """ ushort """
        gets = struct.unpack(self.order + "H", value)
        return gets[0]


Native = ByteOrder("@")
BigEndian = ByteOrder(">")
LittleEndian = ByteOrder("<")
Network = ByteOrder("!")


class ByteOrderStream:
    """ read/write number in specific ByteOrder format """

    def __init__(self, order, stream):
        self.stream = stream
        self.order = order

    def write_uint(self, value):
        """ uint """
        return self.stream.write(self.order.write_uint(value))

    def write_ushort(self, value):
        """ ushort """
        return self.stream.write(self.order.write_ushort(value))

    def write_ns(self, value):
        """ Time of most recent access expressed in nanoseconds as an (long) integer. """
        seconds, remain = constant.parse_nanoseconds(value)
        self.write_uint(seconds)
        self.write_uint(remain)

    def read_uint(self):
        """ uint """
        return self.order.read_uint(self.stream.read(4))

    def read_ushort(self):
        """ ushort """
        return self.order.read_ushort(self.stream.read(2))

    def read_ns(self):
        """ Time of most recent access expressed in nanoseconds as an (long) integer. """
        seconds = self.read_uint()
        remain = self.read_uint()
        return constant.combine_nanoseconds(seconds, remain)


class TeeStream:
    """ Stream Pipe, just like tee """

    def __init__(self, fin, fout):
        self.fin = fin
        self.fout = fout

    def read(self, *args, **kwargs):
        """ read from fin then write to fout """
        ret = self.fin.read(*args, **kwargs)
        self.fout.write(ret)
        return ret


class CloneWriter:
    """ Multiple Writer """

    def __init__(self, *writers):
        self.writers = writers

    def write(self, *args, **kwargs):
        """ write to all stream """
        for writer in self.writers:
            writer.write(*args, **kwargs)
