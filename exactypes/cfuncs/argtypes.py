import _ctypes
import contextlib
import ctypes
import sys
import typing

import typing_extensions

from ..types import CT as _CT
from ..types import PT as _PT
from ..types import CArgObject as _CArgObject

py_object = typing.Annotated[typing.Union[_PT, ctypes.py_object], ctypes.py_object]
c_short = typing.Annotated[typing.Union[int, ctypes.c_short], ctypes.c_short]
c_ushort = typing.Annotated[typing.Union[int, ctypes.c_ushort], ctypes.c_ushort]
c_long = typing.Annotated[typing.Union[int, ctypes.c_long], ctypes.c_long]
c_ulong = typing.Annotated[typing.Union[int, ctypes.c_ulong], ctypes.c_ulong]
c_int = typing.Annotated[typing.Union[int, ctypes.c_int], ctypes.c_int]
c_uint = typing.Annotated[typing.Union[int, ctypes.c_uint], ctypes.c_uint]
c_float = typing.Annotated[typing.Union[float, ctypes.c_float], ctypes.c_float]
c_double = typing.Annotated[typing.Union[float, ctypes.c_double], ctypes.c_double]
c_longdouble = typing.Annotated[typing.Union[float, ctypes.c_longdouble], ctypes.c_longdouble]
c_longlong = typing.Annotated[typing.Union[int, ctypes.c_longlong], ctypes.c_longlong]
c_ulonglong = typing.Annotated[typing.Union[int, ctypes.c_ulonglong], ctypes.c_ulonglong]
c_ubyte = typing.Annotated[typing.Union[int, ctypes.c_ubyte], ctypes.c_ubyte]
c_byte = typing.Annotated[typing.Union[int, ctypes.c_byte], ctypes.c_byte]
c_char = typing.Annotated[typing.Union[bytes, ctypes.c_char], ctypes.c_char]
c_char_p = typing.Annotated[typing.Union[bytes, None, ctypes.c_char_p], ctypes.c_char_p]
c_void_p = typing.Annotated[typing.Union[int, ctypes.c_void_p], ctypes.c_void_p]
c_bool = typing.Annotated[typing.Union[bool, ctypes.c_bool], ctypes.c_bool]
c_wchar_p = typing.Annotated[typing.Union[str, None, ctypes.c_wchar_p], ctypes.c_wchar_p]
c_wchar = typing.Annotated[typing.Union[str, ctypes.c_wchar], ctypes.c_wchar]
c_size_t = typing.Annotated[typing.Union[int, ctypes.c_size_t], ctypes.c_size_t]
c_ssize_t = typing.Annotated[typing.Union[int, ctypes.c_ssize_t], ctypes.c_ssize_t]
c_int8 = typing.Annotated[typing.Union[int, ctypes.c_int8], ctypes.c_int8]
c_uint8 = typing.Annotated[typing.Union[int, ctypes.c_uint8], ctypes.c_uint8]

if sys.version_info >= (3, 12):
    c_time_t = typing.Annotated[typing.Union[int, ctypes.c_time_t], ctypes.c_time_t]
    HAS_TIME_T = True
else:
    HAS_TIME_T = False

HAS_INT16 = HAS_INT32 = HAS_INT64 = False
with contextlib.suppress(AttributeError):
    c_int16 = typing.Annotated[typing.Union[int, ctypes.c_int16], ctypes.c_int16]
    c_uint16 = typing.Annotated[typing.Union[int, ctypes.c_uint16], ctypes.c_uint16]
    HAS_INT16 = True
with contextlib.suppress(AttributeError):
    c_int32 = typing.Annotated[typing.Union[int, ctypes.c_int32], ctypes.c_int32]
    c_uint32 = typing.Annotated[typing.Union[int, ctypes.c_uint32], ctypes.c_uint32]
    HAS_INT32 = True
with contextlib.suppress(AttributeError):
    c_int64 = typing.Annotated[typing.Union[int, ctypes.c_int64], ctypes.c_int64]
    c_uint64 = typing.Annotated[typing.Union[int, ctypes.c_uint64], ctypes.c_uint64]
    HAS_INT64 = True

if typing.TYPE_CHECKING:
    Pointer: typing_extensions.TypeAlias = typing.Union[_ctypes._Pointer[_CT], _CArgObject]
else:
    class Pointer:
        def __class_getitem__(cls, pt: type[_CT]) -> type["_ctypes._Pointer[_CT]"]:
            if isinstance(pt, str):
                return typing.cast(type["_ctypes._Pointer[_CT]"], f"P[{pt!s}]")
            return typing.cast(type["_ctypes._Pointer[_CT]"], ctypes.POINTER(pt))