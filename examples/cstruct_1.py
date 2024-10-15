from __future__ import annotations

import ctypes
import typing

from exactypes.cdataobject import P, cstruct
from exactypes.cdataobject.datafield import c_double, c_int, value


@cstruct()
class A1(ctypes.Structure):
    a: c_int = value()
    _padding: typing.ClassVar[c_int]
    b: c_double = value()
    m: P["A1"] = value()  # noqa: UP037


assert A1._fields_ == (
    ("a", ctypes.c_int),
    ("_padding", ctypes.c_int),
    ("b", ctypes.c_double),
    ("m", P[A1]),
)

a = A1(123, 246, P())
assert a.a == 123
assert a.b == 246.0
assert not bool(a.m)
a.m = P(a)
assert bool(a.m)
assert a.m.contents.a == 123
assert a.m.contents.m.contents.b == 246.0

b = A1(133, m=P(a))
assert b.a == 133
assert b.b == 0.0
assert b.m.contents.b == a.b
