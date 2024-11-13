import ctypes
import typing

# from weakref import WeakValueDictionary
import typing_extensions

if typing.TYPE_CHECKING:
    import _ctypes

    CData: typing_extensions.TypeAlias = "_ctypes._CData"
    CArgObject: typing_extensions.TypeAlias = "_ctypes._CArgObject"
    PyCPointerType = _ctypes._Pointer
else:
    (CData,) = (_o for _o in ctypes._SimpleCData.__mro__ if _o.__name__ == "_CData")
    CArgObject = type(ctypes.byref(ctypes.c_int()))
    PyCPointerType = type(ctypes.POINTER(ctypes.c_int))

CTypes = typing.Union[CData, ctypes.Structure, ctypes.Union, PyCPointerType]

_CT = CT = typing.TypeVar("_CT", bound=CData)
_PT = PT = typing.TypeVar("_PT")
_XCT = XCT = typing.TypeVar("_XCT", bound=CTypes)

CObjOrPtr: typing_extensions.TypeAlias = typing.Union[CData, PyCPointerType]
CDataObjectWrapper: typing_extensions.TypeAlias = typing.Callable[[type[CT]], type[CT]]
StructUnionType: typing_extensions.TypeAlias = typing.Union[
    type[ctypes.Structure], type[ctypes.Union]
]


class SupportsBool(typing_extensions.Protocol):
    def __bool__(self) -> bool: ...


# SupportsDictOrOp: typing_extensions.TypeAlias = typing.Union[
#     dict[str, typing.Any], WeakValueDictionary[str, typing.Any]
# ]
