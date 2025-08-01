from __future__ import annotations

import ctypes
import typing
from collections.abc import Callable

from test_utils import libc
from typing_extensions import assert_type

from exactypes.cfuncs import CFnType, argtypes, ccall, restype

if typing.TYPE_CHECKING:
    from exactypes.types import CArgObject

A = CFnType[[argtypes.c_int, argtypes.c_char_p, argtypes.c_wchar_p], restype.c_longdouble]

assert A._argtypes_ == (ctypes.c_int, ctypes.c_char_p, ctypes.c_wchar_p)
assert A._restype_ == ctypes.c_longdouble

assert_type(
    A().__call__,
    Callable[[argtypes.c_int, argtypes.c_char_p, argtypes.c_wchar_p], restype.c_longdouble],
)

B = CFnType[[argtypes.c_int, argtypes.c_char_p], None]

assert B._argtypes_ == (ctypes.c_int, ctypes.c_char_p)
assert B._restype_ is None


@ccall(libc, override_name="strtod")
def bytes_to_float(  # pyright: ignore[reportRedeclaration]
    ss: argtypes.c_char_p, se: argtypes.ArgPtr[ctypes.c_char_p]
) -> restype.c_double: ...


assert bytes_to_float.argtypes == (ctypes.c_char_p, argtypes.ArgPtr[ctypes.c_char_p])
assert bytes_to_float.restype == ctypes.c_double

cp = ctypes.c_char_p()
assert -1e-7 < bytes_to_float(b"1203.46lalala", se=ctypes.byref(cp)) - 1203.46 < 1e-7
assert cp.value == b"lalala"


@bytes_to_float.errcheck
def bytes_to_float(ret: float, _, args: tuple) -> tuple[float, bytes | None]:
    ret = typing.cast("float", ret)
    _orig, rest = typing.cast("tuple[ctypes.c_char_p, CArgObject]", args)
    return ret, typing.cast("ctypes.c_char_p", getattr(rest, "_obj")).value

assert bytes_to_float(b"1203.46lalala", se=ctypes.byref(cp)) == (1203.46, b"lalala")
