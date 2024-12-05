"""
This test shows forward reference resolving ability.
"""
# from __future__ import annotations

import ctypes
import typing

from exactypes import Ptr, cstruct
from exactypes import datafield as D


@cstruct()
class A1(ctypes.Structure):
    a: D.c_int
    _padding: typing.ClassVar[D.c_int]
    b: D.c_double
    m: Ptr["A2"]
    n: Ptr["A1"]


@cstruct()
class A2(ctypes.Structure):
    a: typing.Annotated[D.c_int, 8]
    b: typing.Annotated[D.c_int, 8]
    c: typing.Annotated[D.c_int, 8]
    d: typing.Annotated[D.c_int, 8]


print(A1._fields_)
print(A2._fields_)

b = A2(a=12, b=13, c=14, d=25)
# b2 = A2(a=12, b=13, c=14, d=25)
# assert b == b2
a = A1(113, 154, Ptr(b), Ptr())
a.n = Ptr(a)
print(f"{a.a = }")
print(f"{a.b = }")
print(f"{a.n.contents.m.contents.d = }")
