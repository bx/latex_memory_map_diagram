#!/usr/bin/env python2

# The MIT License (MIT)
# Copyright (c) 2018 Rebecca ".bx" Shapiro

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import sys
import os
import csv
import generate_mem_diagram as gmd


def set_config(f, typ, key, value, name=None):
    cname = "config"
    lines = []
    with open(f, "r") as fopen:
        lines = fopen.readlines()

    key_found = False
    with open(f, "w") as fopen:
        lineno = 1
        for l in lines:
            parts = l.split(",", 3)
            if typ == cname:
                if len(parts) > 1 and (parts[0] == cname) and parts[1] == key:
                    key_found = True
                    parts[2] = value
                    l = ",".join(parts) + "\n"
            elif typ == "node":
                if parts[0] == "node":
                    fields = [o for o in csv.reader([l], delimiter=',')][0]
                    node = gmd.MemoryMapNode.from_csv(fields, lineno)
                    if node.label == name:
                        nodefields = ["type", "kind", "lo", "hi", "label", "comment"]
                        index = nodefields.index(key)

                        res = []
                        for i in range(len(nodefields)):
                            if i == index:
                                res.append(value)
                            else:
                                res.append(fields[i])
                        l = ",".join(res) + "\n"
                        print res
            fopen.write(l)
            lineno += 1
        if not key_found and typ == cname:
            fopen.write("\n%s,%s,%s\n" % (cname, key, value))


if __name__ == "__main__":
    p = argparse.ArgumentParser("updates group of mmap csvs")
    p.add_argument("files", action='store', nargs='*', default=[])
    p.add_argument('-c', '--config', nargs=2, default=None, action='store',
                   help='set config [key] to [value] w/ -c [key] [value]')
    p.add_argument('-n', '--node', nargs=3, default=None, action='store',
                   help='set node named [name] [field] to [value] w/ -n [name] [field] [value]')

    args = p.parse_args()
    for f in args.files:
        if f.endswith("~"):
            continue
        if args.config:
            (k, v) = args.config
            typ = "config"
            n = None
        elif args.node:
            (n, k, v) = args.node
            typ = "node"
        set_config(f, typ, k, v, n)
