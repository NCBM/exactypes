import contextlib
import ctypes
import sys
import types
import typing
from collections.abc import Iterable, Iterator, MutableSequence, Sequence
from weakref import WeakValueDictionary

import typing_extensions

from .exceptions import AnnotationError, ArrayUntyped
from .types import PT as _PT
from .types import XCT as _XCT
from .types import CTypes, PyCPointerType

array_content_limits: int = 8

_SCT = typing_extensions.TypeVar("_SCT", bound=ctypes._SimpleCData)


def offset_of(
    cobj: typing.Union["ctypes.Array[_XCT]", "PyCPointerType[_XCT]"], ofs: int
) -> "PyCPointerType[_XCT]":
    tp = cobj._type_
    # return ctypes.POINTER(tp).from_address(ctypes.addressof(cobj) + ofs * ctypes.sizeof(tp))
    ptr = ctypes.cast(cobj, ctypes.c_void_p)
    if ptr.value is None:
        raise ValueError("cannot get an offset of null pointer")
    ptr.value += ofs * ctypes.sizeof(tp)
    return ctypes.cast(ptr, ctypes.POINTER(tp))


_array_type_cache: WeakValueDictionary[type[CTypes], type["Array[CTypes]"]] = WeakValueDictionary()


class Array(MutableSequence[_XCT], typing.Generic[_XCT]):
    _base: type[_XCT]
    _type_: type[ctypes.Array[_XCT]]
    _data: ctypes.Array[_XCT]
    _dynamic: bool

    @property
    def _as_parameter_(self) -> "ctypes.Array[_XCT]":
        return self._data

    def __class_getitem__(cls, tp: type[_XCT]) -> typing.Union[type["Array"], types.GenericAlias]:
        if isinstance(tp, typing.TypeVar) or typing_extensions.get_origin(tp) is not None:
            return types.GenericAlias(cls, tp)
        if hasattr(cls, "_base"):
            raise AnnotationError("typed array should not be annotated again")
        array_type_cache = typing.cast(
            WeakValueDictionary[type[_XCT], type["Array[_XCT]"]], _array_type_cache
        )
        if tp in array_type_cache:
            return array_type_cache[tp]
        return array_type_cache.setdefault(tp, type(cls.__name__, (cls,), {"_base": tp}))

    @typing.overload
    def __init__(
        self,
        data: typing.Optional[Iterable[_XCT]] = None,
        *,
        length: int,
        dynamic: typing.Literal[False] = False,
    ) -> None: ...

    @typing.overload
    def __init__(
        self,
        data: Iterable[_XCT],
        *,
        length: typing.Literal[None] = None,
        dynamic: bool = False,
    ) -> None: ...

    @typing.overload
    def __init__(
        self,
        data: typing.Literal[None] = None,
        *,
        length: typing.Literal[None] = None,
        dynamic: typing.Literal[True] = True,
    ) -> None: ...

    def __init__(
        self,
        data: typing.Optional[Iterable[_XCT]] = None,
        *,
        length: typing.Optional[int] = None,
        dynamic: bool = False,
    ) -> None:
        if not hasattr(self, "_base"):
            raise ArrayUntyped(
                f"array not typed! use `{self.__class__.__name__}[some_type]` "
                "to setup a type first."
            )
        if data is not None and not isinstance(data, Sequence):
            data = list(data)
        dlen = 0 if data is None else len(data)
        if length is not None and dlen > length:
            raise ValueError(f"too many data! given {length = } but len(data) = {dlen}")
        if length is not None and length < 0:
            raise ValueError("array length cannot be less than 0")
        self._type_ = self._base * (length or dlen)
        self._data = self._type_()
        if data is not None:
            self._data[:dlen] = data
        self._dynamic = length is None and (dynamic or not dlen)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        clsname = self.__class__.__name__
        if len(self._data) <= array_content_limits:
            return f"{clsname}[{self._base}]{tuple(self._data[:])}"
        return (
            f"{clsname}[{self._base}]("
            + ", ".join(repr(x) for x in self._data[:array_content_limits])
            + ", ...)"
        )

    @typing.overload
    def __getitem__(self, index: int) -> _XCT: ...

    @typing.overload
    def __getitem__(self, index: slice) -> list[_XCT]: ...

    def __getitem__(self, index: typing.Union[int, slice]) -> typing.Union[_XCT, list[_XCT]]:
        return self._data[index]

    @typing.overload
    def __setitem__(self, index: int, value: _XCT) -> None: ...

    @typing.overload
    def __setitem__(self, index: slice, value: Iterable[_XCT]) -> None: ...

    def __setitem__(self, index, value) -> None:
        if value is self or not isinstance(value, (self._base, int, type(None), Sequence)):
            value = tuple(value)
        self._data[index] = value

    def __delitem__(self, index: typing.Union[int, slice]) -> None:
        if not self._dynamic:
            raise TypeError(
                f"{self.__class__.__name__} does not support deletion. "
                "Initialize with `dynamic=True` if needed."
            )
        if isinstance(index, int):
            orig_index = index
            if index < 0:
                index += len(self._data)
            if index not in range(len(self._data)):
                raise IndexError(f"array index [{orig_index}] out of range({len(self._data)})")
            ctypes.memmove(
                offset_of(self._data, index),
                offset_of(self._data, index + 1),
                ctypes.sizeof(self._base) * (len(self._data) - 1 - index),
            )
            self.resize(len(self._data) - 1)
            return
        elif not isinstance(index, slice):
            raise TypeError("index must be int or slice")
        ss, se, st = index.indices(len(self._data))
        if st < 0:
            ss, se, st = se, ss, -st
        if st == 1:
            ctypes.memmove(
                offset_of(self._data, ss),
                offset_of(self._data, se),
                ctypes.sizeof(self._base) * (len(self._data) - se),
            )
            self.resize(len(self._data) - (se - ss))
            return
        for i in reversed(range(ss, se, st)):
            del self[i]

    def insert(self, index: int, value: _XCT) -> None:
        if not self._dynamic:
            raise TypeError(
                f"{self.__class__.__name__} does not support insertion. "
                "Initialize with `dynamic=True` if needed."
            )
        self.resize(len(self._data) + 1)
        ctypes.memmove(
            offset_of(self._data, index + 1),
            offset_of(self._data, index),
            ctypes.sizeof(self._base) * (len(self._data) - index),
        )
        self[index] = value

    def extend(self, values: Iterable[_XCT]) -> None:
        if not self._dynamic:
            raise TypeError(
                f"{self.__class__.__name__} does not support extension. "
                "Initialize with `dynamic=True` if needed."
            )
        if not isinstance(values, (Sequence)):
            values = tuple(values)
        base = len(self._data)
        self.resize(base + len(values))
        self[base:] = values

    def resize(self, size: int):
        self._type_ = self._base * (size)
        self._data = self._type_(*(self._data[:size]))


class _CompatArray(Array[_XCT], typing.Generic[_XCT, _PT]):
    @typing_extensions.no_type_check
    def __class_getitem__(
        cls, tp: tuple[type[_XCT], type[_PT]]
    ) -> typing.Union[type["Array"], types.GenericAlias]:
        return super().__class_getitem__(tp[0])

    if typing.TYPE_CHECKING:

        @typing.overload
        def __init__(
            self,
            data: typing.Optional[Sequence[typing.Union[_XCT, _PT]]] = None,
            *,
            length: int,
            dynamic: typing.Literal[False] = False,
        ) -> None: ...

        @typing.overload
        def __init__(
            self,
            data: Sequence[typing.Union[_XCT, _PT]],
            *,
            length: typing.Literal[None] = None,
            dynamic: bool = False,
        ) -> None: ...

        @typing.overload
        def __init__(
            self,
            data: typing.Literal[None] = None,
            *,
            length: typing.Literal[None] = None,
            dynamic: typing.Literal[True] = True,
        ) -> None: ...

        def __init__(
            self,
            data: typing.Optional[Sequence[typing.Union[_XCT, _PT]]] = None,
            *,
            length: typing.Optional[int] = None,
            dynamic: bool = False,
        ) -> None: ...

        @typing.overload
        def __getitem__(self, index: int) -> _PT: ...

        @typing.overload
        def __getitem__(self, index: slice) -> list[_PT]: ...

        @typing_extensions.no_type_check
        def __getitem__(self, index) -> typing.Union[_PT, list[_PT]]: ...

        @typing_extensions.no_type_check
        def __iter__(self) -> Iterator[_PT]: ...

        @typing_extensions.no_type_check
        def __reversed__(self) -> Iterator[_PT]: ...

        @typing.overload
        def __setitem__(self, index: int, value: typing.Union[_XCT, _PT]) -> None: ...

        @typing.overload
        def __setitem__(self, index: slice, value: Iterable[typing.Union[_XCT, _PT]]) -> None: ...

        def __setitem__(self, index, value) -> None: ...

        def insert(self, index: int, value: typing.Union[_XCT, _PT]) -> None: ...

        def extend(self, values: Iterable[typing.Union[_XCT, _PT]]) -> None: ...

        def append(self, value: typing.Union[_XCT, _PT]) -> None: ...

        def remove(self, value: typing.Any) -> None: ...

        def __iadd__(self, values: Iterable[typing.Union[_XCT, _PT]]) -> typing_extensions.Self: ...


py_object_array = _CompatArray[ctypes.py_object, typing.Any]
c_short_array = _CompatArray[ctypes.c_short, int]
c_ushort_array = _CompatArray[ctypes.c_ushort, int]
c_long_array = _CompatArray[ctypes.c_long, int]
c_ulong_array = _CompatArray[ctypes.c_ulong, int]
c_int_array = _CompatArray[ctypes.c_int, int]
c_uint_array = _CompatArray[ctypes.c_uint, int]
c_float_array = _CompatArray[ctypes.c_float, float]
c_double_array = _CompatArray[ctypes.c_double, float]
c_longdouble_array = _CompatArray[ctypes.c_longdouble, float]
c_longlong_array = _CompatArray[ctypes.c_longlong, int]
c_ulonglong_array = _CompatArray[ctypes.c_ulonglong, int]
c_ubyte_array = _CompatArray[ctypes.c_ubyte, int]
c_byte_array = _CompatArray[ctypes.c_byte, int]
c_char_array = _CompatArray[ctypes.c_char, bytes]
c_char_p_array = _CompatArray[ctypes.c_char_p, typing.Optional[bytes]]
c_void_p_array = _CompatArray[ctypes.c_void_p, typing.Optional[int]]
c_bool_array = _CompatArray[ctypes.c_bool, bool]
c_wchar_p_array = _CompatArray[ctypes.c_wchar_p, typing.Optional[str]]
c_wchar_array = _CompatArray[ctypes.c_wchar, str]
c_size_t_array = _CompatArray[ctypes.c_size_t, int]
c_ssize_t_array = _CompatArray[ctypes.c_ssize_t, int]
c_int8_array = _CompatArray[ctypes.c_int8, int]
c_uint8_array = _CompatArray[ctypes.c_uint8, int]

if sys.version_info >= (3, 12):
    c_time_t_array = _CompatArray[ctypes.c_time_t, int]
    HAS_TIME_T = True
else:
    HAS_TIME_T = False

if sys.version_info >= (3, 14):
    c_float_complex_array = _CompatArray[ctypes.c_float_complex, complex]
    c_double_complex_array = _CompatArray[ctypes.c_double_complex, complex]
    c_longdouble_complex_array = _CompatArray[ctypes.c_longdouble_complex, complex]

HAS_INT16 = HAS_INT32 = HAS_INT64 = False
with contextlib.suppress(AttributeError):
    c_int16_array = _CompatArray[ctypes.c_int16, int]
    c_uint16_array = _CompatArray[ctypes.c_uint16, int]

    @typing.overload
    def of(
        tp: typing.Union[typing.Literal["c_int16"], type[ctypes.c_int16]],
    ) -> type[c_int16_array]: ...

    @typing.overload
    def of(
        tp: typing.Union[typing.Literal["c_uint16"], type[ctypes.c_uint16]],
    ) -> type[c_uint16_array]: ...

    HAS_INT16 = True
with contextlib.suppress(AttributeError):
    c_int32_array = _CompatArray[ctypes.c_int32, int]
    c_uint32_array = _CompatArray[ctypes.c_uint32, int]

    @typing.overload
    def of(
        tp: typing.Union[typing.Literal["c_int32"], type[ctypes.c_int32]],
    ) -> type[c_int32_array]: ...

    @typing.overload
    def of(
        tp: typing.Union[typing.Literal["c_uint32"], type[ctypes.c_uint32]],
    ) -> type[c_uint32_array]: ...

    HAS_INT32 = True
with contextlib.suppress(AttributeError):
    c_int64_array = _CompatArray[ctypes.c_int64, int]
    c_uint64_array = _CompatArray[ctypes.c_uint64, int]

    @typing.overload
    def of(
        tp: typing.Union[typing.Literal["c_int64"], type[ctypes.c_int64]],
    ) -> type[c_int64_array]: ...

    @typing.overload
    def of(
        tp: typing.Union[typing.Literal["c_uint64"], type[ctypes.c_uint64]],
    ) -> type[c_uint64_array]: ...

    HAS_INT64 = True


@typing.overload
def of(
    tp: typing.Union[typing.Literal["py_object"], type["ctypes.py_object[typing.Any]"]],
) -> type[py_object_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_short"], type[ctypes.c_short]],
) -> type[c_short_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_ushort"], type[ctypes.c_ushort]],
) -> type[c_ushort_array]: ...


@typing.overload
def of(tp: typing.Union[typing.Literal["c_long"], type[ctypes.c_long]]) -> type[c_long_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_ulong"], type[ctypes.c_ulong]],
) -> type[c_ulong_array]: ...


@typing.overload
def of(tp: typing.Union[typing.Literal["c_int"], type[ctypes.c_int]]) -> type[c_int_array]: ...


@typing.overload
def of(tp: typing.Union[typing.Literal["c_uint"], type[ctypes.c_uint]]) -> type[c_uint_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_float"], type[ctypes.c_float]],
) -> type[c_float_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_double"], type[ctypes.c_double]],
) -> type[c_double_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_longdouble"], type[ctypes.c_longdouble]],
) -> type[c_longdouble_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_longlong"], type[ctypes.c_longlong]],
) -> type[c_longlong_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_ulonglong"], type[ctypes.c_ulonglong]],
) -> type[c_ulonglong_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_ubyte"], type[ctypes.c_ubyte]],
) -> type[c_ubyte_array]: ...


@typing.overload
def of(tp: typing.Union[typing.Literal["c_byte"], type[ctypes.c_byte]]) -> type[c_byte_array]: ...


@typing.overload
def of(tp: typing.Union[typing.Literal["c_char"], type[ctypes.c_char]]) -> type[c_char_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_char_p"], type[ctypes.c_char_p]],
) -> type[c_char_p_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_void_p"], type[ctypes.c_void_p]],
) -> type[c_void_p_array]: ...


@typing.overload
def of(tp: typing.Union[typing.Literal["c_bool"], type[ctypes.c_bool]]) -> type[c_bool_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_wchar_p"], type[ctypes.c_wchar_p]],
) -> type[c_wchar_p_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_wchar"], type[ctypes.c_wchar]],
) -> type[c_wchar_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_size_t"], type[ctypes.c_size_t]],
) -> type[c_size_t_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_ssize_t"], type[ctypes.c_ssize_t]],
) -> type[c_ssize_t_array]: ...


@typing.overload
def of(tp: typing.Union[typing.Literal["c_int8"], type[ctypes.c_int8]]) -> type[c_int8_array]: ...


@typing.overload
def of(
    tp: typing.Union[typing.Literal["c_uint8"], type[ctypes.c_uint8]],
) -> type[c_uint8_array]: ...


if sys.version_info >= (3, 12):

    @typing.overload
    def of(
        tp: typing.Union[typing.Literal["c_time_t"], type[ctypes.c_time_t]],
    ) -> type[c_time_t_array]: ...


if sys.version_info >= (3, 14):

    @typing.overload
    def of(
        tp: typing.Union[typing.Literal["c_float_complex"], type[ctypes.c_float_complex]],
    ) -> type[c_float_complex_array]: ...

    @typing.overload
    def of(
        tp: typing.Union[typing.Literal["c_double_complex"], type[ctypes.c_double_complex]],
    ) -> type[c_double_complex_array]: ...

    @typing.overload
    def of(
        tp: typing.Union[typing.Literal["c_longdouble_complex"], type[ctypes.c_longdouble_complex]],
    ) -> type[c_longdouble_complex_array]: ...


@typing.overload
def of(tp: str) -> type[Array[typing.Any]]: ...


@typing.overload
def of(tp: type[_SCT]) -> type[Array[_SCT]]: ...


@typing.overload
def of(tp: type[_XCT]) -> type[Array[_XCT]]: ...


def of(tp: typing.Union[str, type[CTypes]]):
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
    return Array[tp]
