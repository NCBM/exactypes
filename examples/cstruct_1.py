"""
This test shows ability of parsing annotations with __future__ 'annotations'.
"""
from __future__ import annotations

import ctypes
import typing

from exactypes import Ptr, cstruct
from exactypes import datafield as D


@cstruct()
class A1(ctypes.Structure):
    a: D.c_int = D.value()
    _padding: typing.ClassVar[D.c_int]
    b: D.c_double = D.value()
    m: Ptr["A1"] = D.value()  # noqa: UP037


assert A1._fields_ == (
    ("a", ctypes.c_int),
    ("_padding", ctypes.c_int),
    ("b", ctypes.c_double),
    ("m", Ptr[A1]),
)

a = A1(123, 246, Ptr())
assert a.a == 123
assert abs(a.b - 246.0) < 1e-7
assert not bool(a.m)
a.m = Ptr(a)
assert bool(a.m)
assert a.m.contents.a == 123
assert abs(a.m.contents.m.contents.b - 246.0) < 1e-7

b = A1(133, m=Ptr(a))
assert b.a == 133
assert abs(b.b - 0.0) < 1e-7
assert b.m.contents.b == a.b
