import ctypes
import typing
from collections.abc import Iterable, MutableSequence, Sequence

from .exceptions import ArrayUntyped
from .types import CT as _CT
from .types import PyCPointerType

array_content_limits: int = 8


def offset_of(
    cobj: typing.Union["ctypes.Array[_CT]", "PyCPointerType[_CT]"], ofs: int
) -> "PyCPointerType[_CT]":
    tp = cobj._type_
    # return ctypes.POINTER(tp).from_address(ctypes.addressof(cobj) + ofs * ctypes.sizeof(tp))
    ptr = ctypes.cast(cobj, ctypes.c_void_p)
    if ptr.value is None:
        raise ValueError("cannot get an offset of null pointer")
    ptr.value += ofs * ctypes.sizeof(tp)
    return ctypes.cast(ptr, ctypes.POINTER(tp))


class Array(MutableSequence[_CT], typing.Generic[_CT]):
    _base: type[_CT]
    _type_: type[ctypes.Array[_CT]]
    _data: ctypes.Array[_CT]
    _dynamic: bool

    def __class_getitem__(cls, tp: type[_CT]) -> type["Array"]:
        return type("Array", (cls,), {"_base": tp})

    @typing.overload
    def __init__(
        self,
        data: typing.Optional[Sequence[_CT]] = None,
        *,
        length: int,
        dynamic: typing.Literal[False] = False,
    ) -> None: ...

    @typing.overload
    def __init__(
        self,
        data: Sequence[_CT],
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
        data: typing.Optional[Sequence[_CT]] = None,
        *,
        length: typing.Optional[int] = None,
        dynamic: bool = False,
    ) -> None:
        if not hasattr(self, "_base"):
            raise ArrayUntyped("array not typed! use `Array[some_type]` to setup a type first.")
        dlen = 0 if data is None else len(data)
        if length is not None and dlen > length:
            raise ValueError(f"too many data! Given {length = } but len(data) = {dlen}")
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
            + ", ".join(str(x) for x in self._data[:array_content_limits])
            + ", ...)"
        )

    @typing.overload
    def __getitem__(self, index: int) -> _CT: ...

    @typing.overload
    def __getitem__(self, index: slice) -> list[_CT]: ...

    def __getitem__(self, index: typing.Union[int, slice]) -> typing.Union[_CT, list[_CT]]:
        return self._data[index]

    @typing.overload
    def __setitem__(self, index: int, value: _CT) -> None: ...

    @typing.overload
    def __setitem__(self, index: slice, value: Iterable[_CT]) -> None: ...

    def __setitem__(self, index, value) -> None:
        if value is self or not isinstance(value, (self._base, int, Sequence)):
            value = tuple(value)
        self._data[index] = value

    def __delitem__(self, index: typing.Union[int, slice]) -> None:
        if not self._dynamic:
            raise TypeError(
                f"{self.__class__.__qualname__} does not support deletion. "
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

    def insert(self, index: int, value: _CT) -> None:
        if not self._dynamic:
            raise TypeError(
                f"{self.__class__.__qualname__} does not support insertion. "
                "Initialize with `dynamic=True` if needed."
            )
        self.resize(len(self._data) + 1)
        ctypes.memmove(
            offset_of(self._data, index + 1),
            offset_of(self._data, index),
            ctypes.sizeof(self._base) * (len(self._data) - index),
        )
        self[index] = value

    def extend(self, values: Iterable[_CT]) -> None:
        if not self._dynamic:
            raise TypeError(
                f"{self.__class__.__qualname__} does not support extension. "
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
