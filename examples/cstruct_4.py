from __future__ import annotations

import ctypes
import typing

from exactypes.cdataobject import cstruct
from exactypes.cdataobject.datafield import array_of, value

char10 = typing.Annotated[array_of("c_char"), 10]
int10 = typing.Annotated[array_of("c_int"), 10]
# char10 = ctypes.c_byte * 10
# int10 = ctypes.c_int * 10


@cstruct
class A6(ctypes.Structure):
    ds1: char10
    ds2: char10
    ds3: int10 = value()


a = A6(b"foo", b"bar")
print(a.ds1, a.ds2, a.ds3)
a.ds3[:3] = [1, 2, 3]
print(a.ds1, a.ds2, a.ds3[:])
