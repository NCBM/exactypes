"""
This test shows ability of default values.
"""
from __future__ import annotations

import ctypes
import typing

from exactypes import cstruct, cunion
from exactypes import datafield as D


@cstruct(defaults=True)
class A4(ctypes.Structure):
    a: D.c_int = D.value(42)
    _padding: typing.ClassVar[D.c_int]
    b: D.c_double = D.value(114.514)


@cunion
class A5(ctypes.Union):
    a: D.c_int = D.value()
    b: D.c_float = D.value()


assert A4._fields_ == (
    ("a", ctypes.c_int),
    ("_padding", ctypes.c_int),
    ("b", ctypes.c_double),
)

a = A4()
assert a.a == 42
assert abs(a.b - 114.514) < 1e-7

b = A5(b=3.14)
assert b.a == 1078523331
