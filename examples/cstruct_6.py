from __future__ import annotations

import ctypes
import struct
from random import randint

from exactypes.cdataobject import cstruct
from exactypes.cdataobject import datafield as D


@cstruct
class A7(ctypes.Structure):
    length: D.c_size_t
    content: D.CFlexibleArray[ctypes.c_char]


BODYSIZE = 256
dtsize = BODYSIZE - ctypes.sizeof(ctypes.c_size_t)
testdata = bytes(randint(0, 255) for _ in range(dtsize))

buf = ctypes.create_string_buffer(struct.pack("@N", dtsize) + testdata, BODYSIZE)
castbuf = ctypes.cast(buf, ctypes.POINTER(A7))

assert castbuf.contents.length == dtsize
strat = ctypes.string_at(castbuf.contents.content, castbuf.contents.length)
assert strat == testdata, f"{strat}\n{testdata}"
