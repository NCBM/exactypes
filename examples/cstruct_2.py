# from __future__ import annotations

import ctypes
import typing

from exactypes.cdataobject import P, cstruct
from exactypes.cdataobject.datafield import c_double, c_int


@cstruct()
class A1(ctypes.Structure):
    a: c_int
    _padding: typing.ClassVar[c_int]
    b: c_double
    m: P["A2"]
    n: P["A1"]


@cstruct()
class A2(ctypes.Structure):
    a: typing.Annotated[c_int, 8]
    b: typing.Annotated[c_int, 8]
    c: typing.Annotated[c_int, 8]
    d: typing.Annotated[c_int, 8]


print(A1._exactypes_unresolved_fields_)
print(A1._fields_)
print(A2._fields_)

b = A2(a=12, b=13, c=14, d=25)
# b2 = A2(a=12, b=13, c=14, d=25)
# assert b == b2
a = A1(113, 154, ctypes.pointer(b), P())
a.n = ctypes.pointer(a)
print(f"{a.a = }")
print(f"{a.b = }")
print(f"{a.n.contents.m.contents.d = }")
