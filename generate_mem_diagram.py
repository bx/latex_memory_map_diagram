#!/usr/bin/env python
from __future__ import division
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

"""
This script generates a memory diagram in LaTeX based off a csv input file.

There are 4 valid types of rows in the csv:

* node: this type of row defines a memory region
* regionlabel: this type of row defines a label for a single memory region
* multiregionlabel
* config

node rows must be formatted as follows:

node, [type], (start address of memory region), (end address of memory region), (label), (comment)

* [type] must be one of the following: notmapped, reserved, regular, registers
* the start and end address can be formated as hexidecimal (beginning with 0x) or decimal
* the label is a unique string to name that region and is optional
* the comment is optional, but it gets printed inside the memory region on the diagram

regionlabel rows must be formatted as follows
regionlabel, (node label), (comment)
* (node label) refers to the label of an existing region, which ever region we want to add a label to
* (comment) is is what is printed on the diagram as a label

generage_mem_diagram.py excepts the following arguments:

* -i / --in : the path of the csv input file from which to generate a diagram
* -r / --preamble: print required latex preamble statements and quit
* -s / --scale: factor in which to scale image
"""

import argparse, csv, sys, os, re, random, string


class TikzTemplate():
    preamble = r"""
\usetikzlibrary{shapes, shapes.geometric, patterns,
                decorations.pathreplacing, calc, positioning}

\tikzset{regionnum/.style={
    rectangle, fill=white, fill opacity=0.4, text opacity=1, font=\tiny,
    outer sep=0.2em,inner sep=0.2em,
    }
}
\tikzset{one sided/.style={
    draw=none,
        append after command={
            [shorten <= -0.5\pgflinewidth]
           ([shift={(-1.5\pgflinewidth,-0.5\pgflinewidth)}]\tikzlastnode.north east)
        ([shift={( 0.5\pgflinewidth,-0.5\pgflinewidth)}]\tikzlastnode.north west)
            ([shift={( 0.5\pgflinewidth,-0.5\pgflinewidth)}]\tikzlastnode.north west)
        ([shift={( 0.5\pgflinewidth,+0.5\pgflinewidth)}]\tikzlastnode.south west)
            ([shift={( 0.5\pgflinewidth,+0.5\pgflinewidth)}]\tikzlastnode.south west)
        edge([shift={(-1.0\pgflinewidth,+0.5\pgflinewidth)}]\tikzlastnode.south east)
        }
  }
}
\tikzset{empty/.style={
    draw=none,
        append after command={
            [shorten <= -0.5\pgflinewidth]
           ([shift={(-1.5\pgflinewidth,-0.5\pgflinewidth)}]\tikzlastnode.north east)
        ([shift={( 0.5\pgflinewidth,-0.5\pgflinewidth)}]\tikzlastnode.north west)
            ([shift={( 0.5\pgflinewidth,-0.5\pgflinewidth)}]\tikzlastnode.north west)
        edge ([shift={( 0.5\pgflinewidth,+0.5\pgflinewidth)}]\tikzlastnode.south west)
            ([shift={( 0.5\pgflinewidth,+0.5\pgflinewidth)}]\tikzlastnode.south west)
        ([shift={(-0.5\pgflinewidth,+0.5\pgflinewidth)}]\tikzlastnode.south east)
       edge ([shift={(-0.5\pgflinewidth,0\pgflinewidth)}]\tikzlastnode.north east)
        }
  }
}

\tikzset{grow up/.style={
    draw=none, very thick, text depth=-3mm,
        append after command={
            [shorten <= -0.5\pgflinewidth]
           ([shift={(-1.5\pgflinewidth,-15\pgflinewidth)}]\tikzlastnode.north east)
        edge[very thick, dotted]([shift={( 0.5\pgflinewidth,-15\pgflinewidth)}]\tikzlastnode.north west)
            ([shift={( +1.5\pgflinewidth,-0.5\pgflinewidth)}]\tikzlastnode.north west)
    edge [very thick, solid]([shift={( +1.5\pgflinewidth,+0.5\pgflinewidth)}]\tikzlastnode.south west)
       ([shift={( 0.5\pgflinewidth,+0.5\pgflinewidth)}]\tikzlastnode.south west)
    edge[solid, very thick]([shift={(-1.0\pgflinewidth,+0.5\pgflinewidth)}]\tikzlastnode.south east)
    ([shift={(-1.0\pgflinewidth,0\pgflinewidth)}]\tikzlastnode.south east)
edge[solid, very thick] ([shift={(-1.0\pgflinewidth,0\pgflinewidth)}]\tikzlastnode.north east)
        }
  }
}

\tikzset{grow down/.style={
    draw=none, text depth=3mm,
        append after command={
            [shorten <= -0.5\pgflinewidth]
           ([shift={(-1.5\pgflinewidth,-0.5\pgflinewidth)}]\tikzlastnode.north east)
    edge [solid, very thick]([shift={( 0.5\pgflinewidth,-0.5\pgflinewidth)}]\tikzlastnode.north west)
            ([shift={( +1.5\pgflinewidth,-0.5\pgflinewidth)}]\tikzlastnode.north west)
    edge [solid, very thick]([shift={( +1.5\pgflinewidth,+0.5\pgflinewidth)}]\tikzlastnode.south west)
       ([shift={( 0.5\pgflinewidth,+15\pgflinewidth)}]\tikzlastnode.south west)
    edge[dotted, very thick]([shift={(-1.0\pgflinewidth,+15\pgflinewidth)}]\tikzlastnode.south east)
    ([shift={(-1.0\pgflinewidth,0\pgflinewidth)}]\tikzlastnode.south east)
edge[solid, very thick] ([shift={(-1.0\pgflinewidth,0\pgflinewidth)}]\tikzlastnode.north east)
        }
  }
}

\tikzstyle{stack} = []
\tikzstyle{heap} = []
\tikzstyle{notmapped} = [pattern=crosshatch, fill opacity=0.4, text opacity=1]
\tikzstyle{reserved} = [pattern=horizontal lines light gray, fill opacity=0.9, text opacity=1]
\tikzstyle{registers} = [dotted, very thick, pattern=crosshatch dots gray,
    fill opacity=1, text opacity=1]
\tikzstyle{regular} = [fill opacity=0.9, text opacity=1]
\tikzstyle{rempty} = [thin, pattern=checkerboard light gray, fill opacity=0.9, text opacity=1]

\newcommand{\regionlabel}[2]
{
\draw[decorate, decoration={brace, amplitude=5, mirror}, xshift=13em, yshift=0] (#1.north west) -- (#1.south west) node [midway, left, xshift=-5] {#2};
}
\newcommand{\multiregionlabel}[3]
{
\draw[decorate, decoration={brace, amplitude=10, mirror}, xshift=13em, yshift=0] (#1.north west) -- (#2.south west) node [midway, left, xshift=-10] {#3};
}
    """
    picdec = "\\begin{tikzpicture}[node distance=-2*\pgflinewidth, transform canvas={scale=%s}]"
    postamble = r"""\end{tikzpicture}"""
    embed_str = "\\ifthenelse{\\equal{\\tikzexternalrealjob}{\\detokenize{%s}}}{%s}{}"

    def __init__(self, width=0, height=0):
        self.width = width
        self.height = height

    def get_preamble(self, embed=False, filename="", scale=1):
        start = ""
        picdec = (TikzTemplate.picdec % (scale))
        out = ""
        if embed:
            out = start + self.embed_str % (filename, picdec)
        else:
            out = start + picdec
        return out

    def get_postamble(self, embed=False, filename=""):
        postamble = TikzTemplate.postamble
        if embed:
            return self.embed_str % (filename, postamble)
        else:
            return postamble


class MemoryMapNodeTemplate():
    template = "\n\\node[%s] (%s) {%s};"
    standardattr = "rectangle, draw=%s, minimum width=%sem, "\
                   "minimum height=%sem, text height = 1em, "\
                   "inner sep = 1mm, align=center, alias=last,"
    minheight = 1.3

    @classmethod
    def calculate_height(cls, node, memrange, maxheight,
                         fixed_height=False,
                         additional=0):
        if fixed_height:
            return cls.minheight + 0.2
        return max(MemoryMapNodeTemplate.minheight,
                   (additional + ((float(node.hi - node.lo) /
                                   float(memrange)) *
                                  maxheight))*0.5)

    @staticmethod
    def populate_template(node, addresswidth, boxwidth,
                          toplabel, bottomlabel,
                          color="black", reverse=False, memrange=0x100000000,
                          maxheight=1, noaddr=False, nodeindex=0, nodecount=-1,
                          fixed_height=False, region_label=False, substage=None):
        additional = 4 if node.grow else 0
        minheight = MemoryMapNodeTemplate.calculate_height(node,
                                                           memrange, maxheight,
                                                           fixed_height, additional)

        attr = MemoryMapNodeTemplate.standardattr % (color,
                                                     boxwidth, minheight)
        if nodeindex > 0:
            attr += ", below=0 of last,"

        typeattrs = ' '
        extras = ''

        if node.kind.startswith('grow down '):
            typeattrs += 'very thick, '
            node.kind = node.kind[len('grow down'):].strip()
            if not reverse:
                typeattrs += 'grow up,'
                extras = "\n\\draw [->, very thick] ([yshift=-9pt] last.north)"\
                         " -- +(0,0.25);"
            else:
                typeattrs += 'grow down,'
                extras = "\n\\draw [->, very thick] "\
                         "([yshift=9pt] last.south) -- +(0,-0.25);"
        if node.kind.startswith('grow up '):
            node.kind = node.kind[len('grow up'):].strip()
            if not reverse:
                typeattrs += 'grow down,'
                extras = "\n\\draw [->, very thick] "\
                         "([yshift=9pt] %s.south) -- +(0,-0.25);" % node.node_id
            else:
                typeattrs += 'grow up,'
                extras = "\n\\draw [->, very thick] "\
                         "([yshift=-9pt] %s.north) -- +(0,0.25);" % node.node_id
        else:
            typeattrs += node.kind
        attr += typeattrs
        node.kind = typeattrs
        labels = ""
        if toplabel or bottomlabel:
            labels = ", append after "\
                     "command = {\\pgfextra {\\let \\mainnode=\\tikzlastnode} %s \n}"
            topbot = ""
            if not reverse:
                top = node.lo
                bottom = node.hi
            else:
                top = node.hi
                bottom = node.lo
            if not noaddr:
                if toplabel:
                    yshift = "-0.5em" if nodecount > 1 and nodeindex == 0 else "0"
                    formatted = ('0x{0:0%dX}' % (addresswidth*2)).format(top) if not noaddr else ''
                    topbot += ("\n\tnode [align=left, anchor=mid west, yshift=%s, "
                               "outer ysep=0, inner ysep=0, "
                               "font=\\fontsize{.15cm}{.1cm}\\selectfont\\tt] "
                               "at (\\mainnode.north east) {%s}" % (yshift, formatted))
                if bottomlabel:
                    yshift = "0.5em" if nodecount > 1 and (nodeindex + 1) == nodecount else "0"
                    formatted = ('0x{0:0%dX}' %
                                 (addresswidth * 2)).format(bottom) if not noaddr else ''
                    topbot += ("\n\tnode [align=left, anchor=mid west, yshift=%s,"
                               "outer ysep=0, inner ysep=0, "
                               "font=\\fontsize{.15cm}{.1cm}\\selectfont\\tt] "
                               "at (\\mainnode.south east) {%s}" % (yshift, formatted))
                labels = labels % topbot
            else:
                labels = ""
        attr += labels
        if region_label:
            extras += "\n\\node[regionnum, "\
                      "anchor=south east] "\
                      "(lab%s) at "\
                      "(%s.south east) {$r_{%s}$};\n" % (nodeindex,
                                                         node.node_id,
                                                         nodeindex)
        return MemoryMapNodeTemplate.template % (attr,
                                                 node.node_id,
                                                 node.comment) + extras


class MemoryMapNode():
    def __init__(self, lo, hi, kind, label="", comment="", number=-1):
        self.lo = lo
        self.hi = hi
        self.kind = kind
        if label == "":
            self.label = ''.join(random.choice(string.ascii_uppercase +
                                               string.digits)
                                 for _ in range(20))  # generate random label if there is none
        else:
            self.label = label
        self.node_id = re.sub("\.", "_", self.label)
        self.number = number
        self.comment = "\\vphantom{\\textit{(}}%s\\vphantom{\\textit{)}}" % comment
        if self.kind.startswith('grow down ') or self.kind.startswith('grow up '):
            self.grow = True
        else:
            self.grow = False

    def __str__(self):
        if self.number > 0:
            return "<%d> Region %s : (%x, %x) of type %s {%s};" % (self.number,
                                                                   self.label,
                                                                   -1 if self.lo is None else self.lo,
                                                                   -1 if self.hi is None else self.hi,
                                                                   self.kind,
                                                                   self.comment)
        else:
            return "Region %s : (%x, %x) of type %s {%s}" % (self.label,
                                                             -1 if self.lo is None else self.lo,
                                                             -1 if self.hi is None else self.hi,
                                                             self.kind, self.comment)

    def __repr__(self):
        return self.__str__()

    def check_range(self, reverse):
        if (self.lo is not None) and (self.hi is not None):
            if not (self.hi > self.lo):
                raise Exception("Bad address range at node %s" % self)
        else:
            if reverse:
                if self.hi is None:
                    raise Exception("When high addresses are at the top, all ranges need "
                                    "high address defined, which is missing from %s" % self)
            else:
                if self.lo is None:
                    raise Exception("When low addresses are at the top, all ranges "
                                    "need low address defined, which is missing from %s" % self)

    def check_range_overlap(self, other, reverse):
        self.check_range(reverse)
        other.check_range(reverse)
        if not reverse:  # low addr at top
            if self.lo == other.lo:
                raise Exception("Ranges overlap between [%s, %s]" % (self, other))
            elif self.lo < other.lo:  # self is definitely lower
                if self.hi is not None:
                    if not (self.hi <= other.lo):  # check self ends before other starts
                        raise Exception("Ranges overlap between [%s, %s]" % (self, other))
            else:  # self.lo > other.lo
                if other.hi is not None:
                    if not (other.hi <= self.lo):
                        raise Exception("Ranges overlap between [%s, %s]" % (self, other))
        else:  # high addr ranges at top
            if self.hi == other.hi:
                raise Exception("Ranges overlap between [%s, %s]" % (self, other))
            elif self.hi < other.hi:  # self is definitely lower
                if other.lo is not None:
                    if not (other.lo >= self.hi):  # check self ends before other starts
                        raise Exception("Ranges overlap between [%s, %s]" % (self, other))
            else:  # self.hi > other.hi
                if self.lo is not None:
                    if not (self.lo >= other.hi):
                        raise Exception("Ranges overlap between [%s, %s]" % (self, other))

    def compareascend(self, other):  # l ow ranges before high range
        self.check_range_overlap(other, False)
        return self.lo - other.lo

    def comparedescend(self, other):  # high ranges before low ranges
        self.check_range_overlap(other, True)
        return other.hi - self.hi

    def compare(self, other):
        if self.hi - self.lo < 0:
            raise Exception("bad range for %s" % (self))
        if other.hi - other.lo < 0:
            raise Exception("bad range for %s" % (other))
        if self.lo > other.lo:  # possible 1
            if self.lo >= other.hi:
                return 1
            else:
                raise Exception("overlapping ranges between [%s, %s]" % (self, other))
        elif self.lo < other.lo:  # possible -1
            if self.hi <= other.lo:
                return -1
            else:
                raise Exception("overlapping ranges between [%s, %s]" % (self, other))
        else:
            raise Exception("overlapping ranges between [%s, %s]" % (self, other))

    def node_error(self, msg):
        if self.number >= 0:
            return "%s at line %d" % (msg, self.number)
        else:
            return msg

    def check_node(self, reverse):
        if (reverse) and (self.hi is None):
            raise Exception("When high addresses are at the top, all ranges need "
                            "high address defined, which is missing from %s" % self)
        if (not reverse) and (self.lo is None):
            raise Exception("When low addresses are at the top, all ranges need low "
                            "address defined, which is missing from %s" % self)
        if (self.lo is not None) and self.lo < 0:
            raise Exception(self.node_error("Region's start address must be non-negative at %s" %
                                            self))
        if (self.hi is not None) and self.hi < 0:
            raise Exception(self.node_error("Region's end address must be non-negativeat %s" %
                                            self))
        if ((self.lo is not None) and (self.hi is not None)) and (self.lo >= self.hi):
            raise Exception(self.node_error("Region's end address must be greater "
                                            "than its  start address at %s") % self)
        self.checked = True

    @staticmethod
    def from_csv(row, lineno):
        return MemoryMapNode(None if row[2].strip() == '' else int(row[2].strip(), 0),
                             None if row[3].strip() == '' else int(row[3].strip(), 0),
                             row[1].strip(), row[4].strip(),
                             ",".join(row[5:]), number=lineno)


class BlankRegionNode(MemoryMapNode):
    def __init__(self, lo, hi):
        MemoryMapNode.__init__(self, lo, hi, "rempty")
        self.uselabels = False


class MemoryMapLabel():
    def __init__(self, comment, number=-1):
        self.number = number
        self.comment = comment

    def label_error(self, msg):
        if self.number >= 0:
            return "%s at line %d" % (msg, self.number)
        else:
            return msg


class MemoryMapRegionLabel(MemoryMapLabel):
    def __init__(self, nodeid, comment, number=-1):
        self.nodeid = nodeid
        MemoryMapLabel.__init__(self, comment, number)

    def node_ids(self):
        return [self.nodeid]

    def to_latex(self):
        return "\\regionlabel{%s}{%s};" % (self.nodeid, self.comment)

    @staticmethod
    def from_csv(row, lineno):
        return MemoryMapRegionLabel(row[1].strip(), ",".join(row[2:]), number=lineno)


class MemoryMapMultiRegionLabel(MemoryMapLabel):
    def __init__(self, topnode, bottomnode, comment, number=-1):
        self.topnode = topnode
        self.bottomnode = bottomnode
        MemoryMapLabel.__init__(self, comment, number)

    def node_ids(self):
        return [self.topnode, self.bottomnode]

    def to_latex(self):
        return "\\multiregionlabel{%s}{%s}{%s};" % (self.topnode, self.bottomnode, self.comment)

    @staticmethod
    def from_csv(row, lineno):
        return MemoryMapMultiRegionLabel(row[1].strip(),
                                         row[2].strip(),
                                         ",".join(row[3:]),
                                         number=lineno)


class MemoryMapParser():
    def __init__(self, infile):
        self.nodes = []
        self.labels = []
        self.infile = infile

    def check_nodes(self, reverse):
        for n in self.nodes:
            n.check_node(reverse)

    def sort_and_check_nodes(self, reverse):
        if not reverse:  # low at top, high at bottom
            nodes = sorted(self.nodes, cmp=MemoryMapNode.compareascend)
        else:  # high at top, low at bottom
            nodes = sorted(self.nodes, cmp=MemoryMapNode.comparedescend)

        last = None
        for n in nodes:
            n.check_node(reverse)
        if nodes:
            last = nodes[0]
        for i in range(1, len(nodes)):
            n = nodes[i]
            if not reverse:  # low at top, high at bottom
                if last.hi and (n.lo > (last.hi+1)):  # if there is a gap, fill it
                    nodes.append(BlankRegionNode(last.hi, n.lo))
            else:  # high on top, low on bottom
                if last.lo and (n.hi < (last.lo-1)):  # if there is a gap, fill it
                    nodes.append(BlankRegionNode(n.hi, last.lo))
            last = n

        # sort with new nodes added
        if not reverse:  # low at top, high at bottom
            self.nodes = sorted(nodes, cmp=MemoryMapNode.compareascend)
        else:  # high at top, low at bottom
            self.nodes = sorted(nodes, cmp=MemoryMapNode.comparedescend)
        self.fill_gaps(reverse)

    def fill_gaps(self, reverse):  # assume that the nodes are sorted at this point
        if self.nodes:
            last = self.nodes[0]
        for n in self.nodes[1:]:
            if not reverse:  # low before high
                if last.hi is None:
                    last.hi = n.lo - 1
            else:  # high before low
                if n.lo is None:
                    n.lo = last.hi-1
            last = n

    def check_labels(self):
        for l in [l for label in self.labels for l in label.node_ids()]:
            if l not in [n.label for n in self.nodes]:
                raise Exception("Node with label %s does not exist" % l)


class MemoryMapConfig():
    def __init__(self, key, value, number=-1):
        self.key = key
        self.value = value
        self.number = number

    @staticmethod
    def from_csv(row, lineno):
        return MemoryMapConfig(row[1].strip(), ",".join(row[2:]), number=lineno)


class MemoryMapCSVParser(MemoryMapParser):
    def parse(self):
        self.config = {}
        with open(self.infile, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            i = 0
            for row in reader:
                if row and row[0].strip() == 'node':
                    self.nodes.append(MemoryMapNode.from_csv(row, i))
                elif row and row[0].strip() == 'regionlabel':
                    self.labels.append(MemoryMapRegionLabel.from_csv(row, i))
                elif row and row[0].strip() == 'multiregionlabel':
                    self.labels.append(MemoryMapMultiRegionLabel.from_csv(row, i))
                elif row and row[0].strip() == 'config':
                    c = MemoryMapConfig.from_csv(row, i)
                    self.config[c.key] = c.value
                i += 1


class MemoryMapGenerator():
    def __init__(self, infile):
        # self.reverse = reverse
        self.infile = infile
        self.p = MemoryMapCSVParser(self.infile)
        self.p.parse()
        self.embed = True if 'embed' in self.p.config else False
        self.noaddr = True if 'noaddr' in self.p.config else False
        # 'size of an address in bits (must be a multiple of 8)'
        self.buswidth = 32 if 'buswidth' not in self.p.config else int(self.p.config.get('buswidth'))
        self.height = float(self.p.config.get('height', 70))
        # Width of region box on diagram in em(default = 7em)
        #xsself.scale = 1 if 'scale' not in self.p.config else float(self.p.config.get('scale'))
        self.reverse = True if 'reverse' in self.p.config else False
        # diagram height
        # full width?
        self.width = float(self.p.config.get('width', '8'))
        self.fixed = True if 'fixed' in self.p.config else False
        self.label_rnum = True if 'region_label' in self.p.config else False
        self.label_snum = self.p.config.get('substage_label') \
                          if 'substage_label' in self.p.config else None
        self.p.sort_and_check_nodes(self.reverse)
        self.p.check_labels()

    def generate_node_latex(self, addrwidth,
                            maxheight=20, fixed=False,
                            label_region=False, substage=None):
        o = ""
        for i in range(len(self.p.nodes)):
            n = self.p.nodes[i]
            if not self.reverse:
                if self.p.nodes[0].lo is None:
                    raise Exception("Lowest address must be defined")
                o += MemoryMapNodeTemplate.populate_template(n, addrwidth*2,
                                                             self.width, True,
                                                             i == (len(self.p.nodes)-1),
                                                             "black",
                                                             self.reverse,
                                                             self.p.nodes[-1].hi -
                                                             self.p.nodes[0].lo,
                                                             maxheight, self.noaddr,
                                                             i, len(self.p.nodes),
                                                             fixed, label_region, substage)
            else:
                if self.p.nodes[-1].hi is None:
                    raise Exception("Highest address must be defined")
                o += MemoryMapNodeTemplate.populate_template(n, addrwidth,
                                                             self.width,
                                                             i == 0, True,
                                                             "black",
                                                             self.reverse,
                                                             self.p.nodes[0].hi -
                                                             self.p.nodes[-1].lo,
                                                             maxheight, self.noaddr,
                                                             i, len(self.p.nodes),
                                                             fixed, label_region, substage)
            o += "\n"
        return o

    def generate_region_label_latex(self):
        o = ""
        for l in self.p.labels:
            o += l.to_latex()
            o += "\n"
        return o


if __name__ == "__main__":
    p = argparse.ArgumentParser("Generates Tikz/LaTex-based memory map diagrams from csv")
    p.add_argument('-i', '--in', dest='infile', action='store',
                   help='data from which to generate memory map, must end with *.csv',
                   default='input.csv')
    p.add_argument('-r', '--preamble', action='store_true',
                   help='print required preamble statements and quit', default=False)
    p.add_argument('-s', '--scale', action='store', default=1)
#    p.add_argument("-t", '--tikzoptions', action="store", default="",
#                   help="add this string to tikzpicture environment optional arguments")

    def gen_tex_string(tikztemplate, imagestring, filename="", infile="", scale=1):
        return tikztemplate.get_preamble(m.embed, filename, scale) + \
            imagestring + tikztemplate.get_postamble(m.embed, filename)

    def gen_node_strs(m):
        s = m.generate_node_latex(m.buswidth/8,
                                  m.height,
                                  m.fixed, m.label_rnum, m.label_snum)
        s += "\n"
        s += m.generate_region_label_latex()
        return s

    args = p.parse_args()
    s = ""
    if args.preamble:
        s = TikzTemplate.preamble
    else:

        m = MemoryMapGenerator(args.infile)

        tikztemplate = TikzTemplate(m.width, m.height)
#                                    args.tikzoptions)
        nodestrs = gen_node_strs(m)

        # generate final tex output
        fn = os.path.splitext(os.path.basename(args.infile))[0]
        s = gen_tex_string(tikztemplate, nodestrs, fn, args.infile, float(args.scale))
    print(s)
