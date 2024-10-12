import contextlib
import ctypes
import sys
import typing

from ..types import CT as _CT
from ..types import PT as _PT
from ..types import CData as _CData


class CDataField(typing.Generic[_PT, _CT]):
    def __init__(self, ptype: type[_PT], ctype: type[_CT]) -> None:
        self.ptype = ptype
        self.ctype = ctype

    def __get__(self, obj: _CData, type_: typing.Union[type[_CData], None] = None) -> _PT:  # type: ignore[empty-body]
        ...

    def __set__(self, obj: _CData, value: typing.Union[_PT, _CT]) -> None: ...


py_object = CDataField[_PT, ctypes.py_object]
c_short = CDataField[int, ctypes.c_short]
c_ushort = CDataField[int, ctypes.c_ushort]
c_long = CDataField[int, ctypes.c_long]
c_ulong = CDataField[int, ctypes.c_ulong]
c_int = CDataField[int, ctypes.c_int]
c_uint = CDataField[int, ctypes.c_uint]
c_float = CDataField[float, ctypes.c_float]
c_double = CDataField[float, ctypes.c_double]
c_longdouble = CDataField[float, ctypes.c_longdouble]
c_longlong = CDataField[int, ctypes.c_longlong]
c_ulonglong = CDataField[int, ctypes.c_ulonglong]
c_ubyte = CDataField[int, ctypes.c_ubyte]
c_byte = CDataField[int, ctypes.c_byte]
c_char = CDataField[bytes, ctypes.c_char]
c_char_p = CDataField[typing.Optional[bytes], ctypes.c_char_p]
c_void_p = CDataField[int, ctypes.c_void_p]
c_bool = CDataField[bool, ctypes.c_bool]
c_wchar_p = CDataField[typing.Optional[str], ctypes.c_wchar_p]
c_wchar = CDataField[str, ctypes.c_wchar]
c_size_t = CDataField[int, ctypes.c_size_t]
c_ssize_t = CDataField[int, ctypes.c_ssize_t]
c_int8 = CDataField[int, ctypes.c_int8]
c_uint8 = CDataField[int, ctypes.c_uint8]

if sys.version_info >= (3, 12):
    c_time_t = CDataField[int, ctypes.c_time_t]
    HAS_TIME_T = True
else:
    HAS_TIME_T = False

HAS_INT16 = HAS_INT32 = HAS_INT64 = False
with contextlib.suppress(AttributeError):
    c_int16 = CDataField[int, ctypes.c_int16]
    c_uint16 = CDataField[int, ctypes.c_uint16]
    HAS_INT16 = True
with contextlib.suppress(AttributeError):
    c_int32 = CDataField[int, ctypes.c_int32]
    c_uint32 = CDataField[int, ctypes.c_uint32]
    HAS_INT32 = True
with contextlib.suppress(AttributeError):
    c_int64 = CDataField[int, ctypes.c_int64]
    c_uint64 = CDataField[int, ctypes.c_uint64]
    HAS_INT64 = True
