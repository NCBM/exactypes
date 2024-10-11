import contextlib
import ctypes
import sys
import typing

from ..types import PT as _PT

py_object = typing.Annotated[_PT, ctypes.py_object]
c_short = typing.Annotated[int, ctypes.c_short]
c_ushort = typing.Annotated[int, ctypes.c_ushort]
c_long = typing.Annotated[int, ctypes.c_long]
c_ulong = typing.Annotated[int, ctypes.c_ulong]
c_int = typing.Annotated[int, ctypes.c_int]
c_uint = typing.Annotated[int, ctypes.c_uint]
c_float = typing.Annotated[float, ctypes.c_float]
c_double = typing.Annotated[float, ctypes.c_double]
c_longdouble = typing.Annotated[float, ctypes.c_longdouble]
c_longlong = typing.Annotated[int, ctypes.c_longlong]
c_ulonglong = typing.Annotated[int, ctypes.c_ulonglong]
c_ubyte = typing.Annotated[int, ctypes.c_ubyte]
c_byte = typing.Annotated[int, ctypes.c_byte]
c_char = typing.Annotated[bytes, ctypes.c_char]
c_char_p = typing.Annotated[typing.Optional[bytes], ctypes.c_char_p]
c_void_p = typing.Annotated[int, ctypes.c_void_p]
c_bool = typing.Annotated[bool, ctypes.c_bool]
c_wchar_p = typing.Annotated[typing.Optional[str], ctypes.c_wchar_p]
c_wchar = typing.Annotated[str, ctypes.c_wchar]
c_size_t = typing.Annotated[int, ctypes.c_size_t]
c_ssize_t = typing.Annotated[int, ctypes.c_ssize_t]
c_int8 = typing.Annotated[int, ctypes.c_int8]
c_uint8 = typing.Annotated[int, ctypes.c_uint8]

if sys.version_info >= (3, 12):
    c_time_t = typing.Annotated[int, ctypes.c_time_t]
    HAS_TIME_T = True
else:
    HAS_TIME_T = False

HAS_INT16 = HAS_INT32 = HAS_INT64 = False
with contextlib.suppress(AttributeError):
    c_int16 = typing.Annotated[int, ctypes.c_int16]
    c_uint16 = typing.Annotated[int, ctypes.c_uint16]
    HAS_INT16 = True
with contextlib.suppress(AttributeError):
    c_int32 = typing.Annotated[int, ctypes.c_int32]
    c_uint32 = typing.Annotated[int, ctypes.c_uint32]
    HAS_INT32 = True
with contextlib.suppress(AttributeError):
    c_int64 = typing.Annotated[int, ctypes.c_int64]
    c_uint64 = typing.Annotated[int, ctypes.c_uint64]
    HAS_INT64 = True