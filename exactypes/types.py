import _ctypes
import ctypes
import typing

import typing_extensions

if typing.TYPE_CHECKING:
    CData: typing_extensions.TypeAlias = "_ctypes._CData"
    CArgObject: typing_extensions.TypeAlias = "_ctypes._CArgObject"
    PyCPointerType = _ctypes._Pointer
else:
    (CData,) = (_o for _o in ctypes._SimpleCData.__mro__ if _o.__name__ == "_CData")
    CArgObject = type(ctypes.byref(ctypes.c_int()))
    PyCPointerType = type(ctypes.POINTER(ctypes.c_int))

CTypes: typing_extensions.TypeAlias = typing.Union[
    CData, ctypes.Structure, ctypes.Union, PyCPointerType, ctypes.Array
]
CTYPES = (
    CData,  # pyright: ignore[reportGeneralTypeIssues] # we've already got the real CData type.
    ctypes.Structure,
    ctypes.Union,
    PyCPointerType,
    ctypes.Array,
    _ctypes.CFuncPtr,
)
CDataType: typing_extensions.TypeAlias = typing.Union[
    "ctypes._SimpleCData[typing.Any]",
    "PyCPointerType[typing.Any]",
    _ctypes.CFuncPtr,
    ctypes.Union,
    ctypes.Structure,
    "ctypes.Array[typing.Any]",
]
CDATATYPE = (
    ctypes._SimpleCData,
    PyCPointerType,
    _ctypes.CFuncPtr,
    ctypes.Union,
    ctypes.Structure,
    ctypes.Array,
)

_CT = CT = typing.TypeVar("_CT", bound=CData)
_PT = PT = typing.TypeVar("_PT")
_XCT = XCT = typing.TypeVar("_XCT", bound=CDataType)

# CObjOrPtr: typing_extensions.TypeAlias = typing.Union[CData, PyCPointerType]
CDataObjectWrapper: typing_extensions.TypeAlias = typing.Callable[[type[CT]], type[CT]]
StructUnionType: typing_extensions.TypeAlias = typing.Union[
    type[ctypes.Structure], type[ctypes.Union]
]


class SupportsBool(typing_extensions.Protocol):
    def __bool__(self) -> bool: ...


if typing_extensions.TYPE_CHECKING:
    Ptr: typing_extensions.TypeAlias = "ctypes._Pointer[_XCT]"
else:

    class Ptr:
        def __new__(
            cls, cobj: typing.Union[_XCT, PyCPointerType, None] = None
        ) -> "typing.Union[ctypes._Pointer[_XCT], None]":
            if cobj is None:
                return None
            return ctypes.pointer(cobj)  # type: ignore

        def __class_getitem__(cls, pt: type[_XCT]) -> type["ctypes._Pointer[_XCT]"]:
            if isinstance(pt, str):
                return typing.cast(type["ctypes._Pointer[_XCT]"], f"Ptr[{pt!s}]")
            return typing.cast(type["ctypes._Pointer[_XCT]"], ctypes.POINTER(pt))


# SupportsDictOrOp: typing_extensions.TypeAlias = typing.Union[
#     dict[str, typing.Any], WeakValueDictionary[str, typing.Any]
# ]
