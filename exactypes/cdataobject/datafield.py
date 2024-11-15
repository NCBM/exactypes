import contextlib
import ctypes
import sys
import typing
from collections.abc import MutableSequence

from ..array import Array
from ..types import PT as _PT
from ..types import XCT as _XCT
from ..types import CTypes


class CDataField(typing.Generic[_PT, _XCT]):
    def __init__(self, ptype: type[_PT], ctype: type[_XCT]) -> None:
        self.ptype = ptype
        self.ctype = ctype

    def __get__(self, obj, type_=None) -> _PT:  # type: ignore[empty-body]
        ...

    def __set__(self, obj, value: typing.Union[_PT, _XCT]) -> None: ...


class CArrayField(CDataField[_PT, ctypes.Array[_XCT]], typing.Generic[_PT, _XCT]):
    def __get__(self, obj, type_=None) -> _PT:  # type: ignore[empty-body]
        ...

    def __set__(self, obj, value: typing.Union[_PT, ctypes.Array[_XCT]]) -> None: ...


def value(default: typing.Any = None) -> typing.Any:
    return default


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

py_object_array = CArrayField[MutableSequence[typing.Any], ctypes.py_object]
c_short_array = CArrayField[MutableSequence[int], ctypes.c_short]
c_ushort_array = CArrayField[MutableSequence[int], ctypes.c_ushort]
c_long_array = CArrayField[MutableSequence[int], ctypes.c_long]
c_ulong_array = CArrayField[MutableSequence[int], ctypes.c_ulong]
c_int_array = CArrayField[MutableSequence[int], ctypes.c_int]
c_uint_array = CArrayField[MutableSequence[int], ctypes.c_uint]
c_float_array = CArrayField[MutableSequence[float], ctypes.c_float]
c_double_array = CArrayField[MutableSequence[float], ctypes.c_double]
c_longdouble_array = CArrayField[MutableSequence[float], ctypes.c_longdouble]
c_longlong_array = CArrayField[MutableSequence[int], ctypes.c_longlong]
c_ulonglong_array = CArrayField[MutableSequence[int], ctypes.c_ulonglong]
c_ubyte_array = CArrayField[MutableSequence[int], ctypes.c_ubyte]
c_byte_array = CArrayField[MutableSequence[int], ctypes.c_byte]
c_char_array = CArrayField[bytes, ctypes.c_char]
c_char_p_array = CArrayField[MutableSequence[typing.Optional[bytes]], ctypes.c_char_p]
c_void_p_array = CArrayField[MutableSequence[typing.Optional[int]], ctypes.c_void_p]
c_bool_array = CArrayField[MutableSequence[bool], ctypes.c_bool]
c_wchar_p_array = CArrayField[MutableSequence[typing.Optional[str]], ctypes.c_wchar_p]
c_wchar_array = CArrayField[str, ctypes.c_wchar]
c_size_t_array = CArrayField[MutableSequence[int], ctypes.c_size_t]
c_ssize_t_array = CArrayField[MutableSequence[int], ctypes.c_ssize_t]
c_int8_array = CArrayField[MutableSequence[int], ctypes.c_int8]
c_uint8_array = CArrayField[MutableSequence[int], ctypes.c_uint8]


if sys.version_info >= (3, 12):
    c_time_t = CDataField[int, ctypes.c_time_t]
    c_time_t_array = CArrayField[MutableSequence[int], ctypes.c_time_t]

    # no overload for c_time_t since it is actually c_int32 or c_int64.

    HAS_TIME_T = True
else:
    HAS_TIME_T = False

if sys.version_info >= (3, 14):
    c_float_complex = CDataField[complex, ctypes.c_float_complex]
    c_double_complex = CDataField[complex, ctypes.c_double_complex]
    c_longdouble_complex = CDataField[complex, ctypes.c_longdouble_complex]
    c_float_complex_array = CArrayField[MutableSequence[complex], ctypes.c_float_complex]
    c_double_complex_array = CArrayField[MutableSequence[complex], ctypes.c_double_complex]
    c_longdouble_complex_array = CArrayField[MutableSequence[complex], ctypes.c_longdouble_complex]

    @typing.overload
    def array_of(
        tp: typing.Union[typing.Literal["c_float_complex"], type[ctypes.c_float_complex]],
    ) -> type[c_float_complex_array]: ...

    @typing.overload
    def array_of(
        tp: typing.Union[typing.Literal["c_double_complex"], type[ctypes.c_double_complex]],
    ) -> type[c_double_complex_array]: ...

    @typing.overload
    def array_of(
        tp: typing.Union[typing.Literal["c_longdouble_complex"], type[ctypes.c_longdouble_complex]],
    ) -> type[c_longdouble_complex_array]: ...

HAS_INT16 = HAS_INT32 = HAS_INT64 = False
with contextlib.suppress(AttributeError):
    c_int16 = CDataField[int, ctypes.c_int16]
    c_uint16 = CDataField[int, ctypes.c_uint16]
    c_int16_array = CArrayField[MutableSequence[int], ctypes.c_int16]
    c_uint16_array = CArrayField[MutableSequence[int], ctypes.c_uint16]

    @typing.overload
    def array_of(
        tp: typing.Union[typing.Literal["c_int16"], type[ctypes.c_int16]],
    ) -> type[c_int16_array]: ...

    @typing.overload
    def array_of(
        tp: typing.Union[typing.Literal["c_uint16"], type[ctypes.c_uint16]],
    ) -> type[c_uint16_array]: ...

    HAS_INT16 = True
with contextlib.suppress(AttributeError):
    c_int32 = CDataField[int, ctypes.c_int32]
    c_uint32 = CDataField[int, ctypes.c_uint32]
    c_int32_array = CArrayField[MutableSequence[int], ctypes.c_int32]
    c_uint32_array = CArrayField[MutableSequence[int], ctypes.c_uint32]

    @typing.overload
    def array_of(
        tp: typing.Union[typing.Literal["c_int32"], type[ctypes.c_int32]],
    ) -> type[c_int32_array]: ...

    @typing.overload
    def array_of(
        tp: typing.Union[typing.Literal["c_uint32"], type[ctypes.c_uint32]],
    ) -> type[c_uint32_array]: ...

    HAS_INT32 = True
with contextlib.suppress(AttributeError):
    c_int64 = CDataField[int, ctypes.c_int64]
    c_uint64 = CDataField[int, ctypes.c_uint64]
    c_int64_array = CArrayField[MutableSequence[int], ctypes.c_int64]
    c_uint64_array = CArrayField[MutableSequence[int], ctypes.c_uint64]

    @typing.overload
    def array_of(
        tp: typing.Union[typing.Literal["c_int64"], type[ctypes.c_int64]],
    ) -> type[c_int64_array]: ...

    @typing.overload
    def array_of(
        tp: typing.Union[typing.Literal["c_uint64"], type[ctypes.c_uint64]],
    ) -> type[c_uint64_array]: ...

    HAS_INT64 = True


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["py_object"], type["ctypes.py_object[typing.Any]"]],
) -> type[py_object_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_short"], type[ctypes.c_short]],
) -> type[c_short_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_ushort"], type[ctypes.c_ushort]],
) -> type[c_ushort_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_long"], type[ctypes.c_long]],
) -> type[c_long_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_ulong"], type[ctypes.c_ulong]],
) -> type[c_ulong_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_int"], type[ctypes.c_int]],
) -> type[c_int_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_uint"], type[ctypes.c_uint]],
) -> type[c_uint_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_float"], type[ctypes.c_float]],
) -> type[c_float_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_double"], type[ctypes.c_double]],
) -> type[c_double_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_longdouble"], type[ctypes.c_longdouble]],
) -> type[c_longdouble_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_longlong"], type[ctypes.c_longlong]],
) -> type[c_longlong_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_ulonglong"], type[ctypes.c_ulonglong]],
) -> type[c_ulonglong_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_ubyte"], type[ctypes.c_ubyte]],
) -> type[c_ubyte_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_byte"], type[ctypes.c_byte]],
) -> type[c_byte_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_char"], type[ctypes.c_char]],
) -> type[c_char_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_char_p"], type[ctypes.c_char_p]],
) -> type[c_char_p_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_void_p"], type[ctypes.c_void_p]],
) -> type[c_void_p_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_bool"], type[ctypes.c_bool]],
) -> type[c_bool_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_wchar_p"], type[ctypes.c_wchar_p]],
) -> type[c_wchar_p_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_wchar"], type[ctypes.c_wchar]],
) -> type[c_wchar_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_size_t"], type[ctypes.c_size_t]],
) -> type[c_size_t_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_ssize_t"], type[ctypes.c_ssize_t]],
) -> type[c_ssize_t_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_int8"], type[ctypes.c_int8]],
) -> type[c_int8_array]: ...


@typing.overload
def array_of(
    tp: typing.Union[typing.Literal["c_uint8"], type[ctypes.c_uint8]],
) -> type[c_uint8_array]: ...


@typing.overload
def array_of(tp: type[_XCT]) -> type[CArrayField[_XCT, _XCT]]: ...


@typing.overload
def array_of(tp: str) -> type[CArrayField[typing.Any, typing.Any]]: ...


def array_of(tp):
    if isinstance(tp, str):
        from inspect import currentframe

        fr = currentframe()
        if fr is not None:
            fr = fr.f_back
        ctx: dict[str, CTypes] = fr.f_globals if fr is not None else {}
        if tp not in ctx:
            return globals().get(tp + "_array", Array[getattr(ctypes, tp)])
        return globals().get(tp + "_array", Array[getattr(ctypes, tp, ctx[tp])])
    elif isinstance(tp, ctypes._SimpleCData):
        return globals().get(getattr(tp, "__name__") + "_array", Array[tp])
    return CArrayField[tp, tp]
