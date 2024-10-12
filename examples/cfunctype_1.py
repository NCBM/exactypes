import ctypes

from typing_extensions import reveal_type

from exactypes.cfuncs import CFnType, argtypes, restype

A = CFnType[[argtypes.c_int, argtypes.c_char_p, argtypes.c_wchar_p], restype.c_longdouble]

assert A._argtypes_ == (ctypes.c_int, ctypes.c_char_p, ctypes.c_wchar_p)
assert A._restype_ == ctypes.c_longdouble

reveal_type(A().__call__)