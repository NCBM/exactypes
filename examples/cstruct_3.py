from __future__ import annotations

import ctypes
import typing

from exactypes.cdataobject import cstruct
from exactypes.cdataobject.datafield import c_double, c_int, value


@cstruct(defaults=True)
class A4(ctypes.Structure):
    a: c_int = value(42)
    _padding: typing.ClassVar[c_int]
    b: c_double = value(114.514)


assert A4._fields_ == (
    ("a", ctypes.c_int),
    ("_padding", ctypes.c_int),
    ("b", ctypes.c_double),
)

a = A4()
assert a.a == 42
assert abs(a.b - 114.514) < 1e7
