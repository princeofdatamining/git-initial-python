#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" yet another git """
import sys
from yagit import database


USAGE = """Usage: {prog} WORKDIR <command> [<args>]

Commands:
    add
    cat
    commit
    #diff
    init
    rm
    status
"""


def _usage(prog):
    print(USAGE.format(prog=prog))


def _main(argv):
    try:
        prog = argv.pop(0)
        workdir = argv.pop(0)
        command = argv.pop(0)
    except IndexError:
        _usage(prog)
        return
    else:
        manager = database.Database(workdir)
    #
    try:
        func = getattr(manager, command)
    except AttributeError:
        _usage(prog)
    else:
        func(*argv)
    #


if __name__ == "__main__":
    _main(sys.argv)
