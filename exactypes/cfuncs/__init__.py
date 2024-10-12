import ctypes
import os
import typing
from _ctypes import FUNCFLAG_CDECL as _FUNCFLAG_CDECL
from _ctypes import FUNCFLAG_PYTHONAPI as _FUNCFLAG_PYTHONAPI
from _ctypes import FUNCFLAG_USE_ERRNO as _FUNCFLAG_USE_ERRNO
from _ctypes import FUNCFLAG_USE_LASTERROR as _FUNCFLAG_USE_LASTERROR
from _ctypes import CFuncPtr as _CFuncPtr
from collections.abc import Callable, Sequence

if os.name == "nt":
    from _ctypes import FUNCFLAG_STDCALL as _FUNCFLAG_STDCALL  # type: ignore

import types

import typing_extensions

from ..exceptions import AnnotationError

# from ..types import CT as _CT
from ..types import PT as _PT
from ..types import CData as _CData
from ..types import CObjOrPtr
from ..types import PyCPointerType as _PyCPointerType
from . import argtypes as argtypes
from . import restype as restype

_TVT = typing_extensions.TypeVarTuple("_TVT")
_PS = typing_extensions.ParamSpec("_PS")


def _create_functype(
    name: str,
    restype_: type[CObjOrPtr],
    *argtypes_: type[CObjOrPtr],
    flags: int,
    _cache: typing.Optional[
        dict[tuple[type[CObjOrPtr], tuple[type[CObjOrPtr], ...], int], type[_CFuncPtr]]
    ],
) -> type[_CFuncPtr]:
    _type = type(
        name, (_CFuncPtr,), {"_argtypes_": argtypes_, "_restype_": restype_, "_flags_": flags}
    )
    if _cache is not None:
        _cache[(restype_, argtypes_, flags)] = _type
    return _type


def _create_cfunctype(
    restype_: type[CObjOrPtr],
    *argtypes_: type[CObjOrPtr],
    use_errno: bool = False,
    use_last_error: bool = False,
) -> type[_CFuncPtr]:
    flags = _FUNCFLAG_CDECL
    if use_errno:
        flags |= _FUNCFLAG_USE_ERRNO
    if use_last_error:
        flags |= _FUNCFLAG_USE_LASTERROR
    return _create_functype(
        "CFunctionType",
        restype_,
        *argtypes_,
        flags=flags,
        _cache=ctypes._c_functype_cache,  # pyright: ignore[reportAttributeAccessIssue]
    )


if os.name == "nt":
    def _create_winfunctype(  # type: ignore
        restype_: type[CObjOrPtr],
        *argtypes_: type[CObjOrPtr],
        use_errno: bool = False,
        use_last_error: bool = False,
    ) -> type[_CFuncPtr]:
        flags = _FUNCFLAG_STDCALL  # type: ignore
        if use_errno:
            flags |= _FUNCFLAG_USE_ERRNO
        if use_last_error:
            flags |= _FUNCFLAG_USE_LASTERROR
        return _create_functype(
            "WinFunctionType",
            restype_,
            *argtypes_,
            flags=flags,
            _cache=ctypes._win_functype_cache,  # pyright: ignore[reportAttributeAccessIssue]
        )
else:
    def _create_winfunctype(
        restype_: type[CObjOrPtr],
        *argtypes_: type[CObjOrPtr],
        use_errno: bool = False,
        use_last_error: bool = False,
    ) -> typing_extensions.Never:
        raise RuntimeError("`WinFunctionType` can only be created on Windows platform.")


def _create_pyfunctype(restype_: type[CObjOrPtr], *argtypes_: type[CObjOrPtr]) -> type[_CFuncPtr]:
    flags = _FUNCFLAG_CDECL | _FUNCFLAG_PYTHONAPI
    return _create_functype("CFunctionType", restype_, *argtypes_, flags=flags, _cache=None)


def _digest_annotated_types(*types_: type) -> tuple[type[CObjOrPtr], ...]:
    res: list[type[CObjOrPtr]] = []
    for tp in types_:
        if isinstance(tp, (types.GenericAlias, typing._GenericAlias)):  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
            _, tp = typing.cast(tuple[typing.Any, type], typing_extensions.get_args(tp))

        if issubclass(tp, (_CData, _PyCPointerType)):
            res.append(tp)
            continue

        if not issubclass(tp, (_CData, _PyCPointerType)):
            raise AnnotationError(f"Bad annotation type '{tp!s}'.")
        
        res.append(tp)
    return tuple(res)


if typing.TYPE_CHECKING:
    _PF: typing_extensions.TypeAlias = typing.Union[tuple[int], tuple[int, typing.Optional[str]], tuple[int, typing.Optional[str], typing.Any]]
    _ECT: typing_extensions.TypeAlias = Callable[[typing.Optional[_CData], _CFuncPtr, tuple[_CData, ...]], _CData]
    class CFnType(_CFuncPtr, typing.Generic[_PS, _PT]):
        _restype_: typing.Union[type[_CData], Callable[[int], typing.Any], None]
        _argtypes_: Sequence[type[_CData]]
        errcheck: _ECT
        # Abstract attribute that must be defined on subclasses
        _flags_: typing.ClassVar[int]
        @typing.overload
        def __init__(self) -> None: ...
        @typing.overload
        def __init__(self, address: int, /) -> None: ...
        @typing.overload
        def __init__(self, callable: Callable[_PS, _PT], /) -> None: ...
        @typing.overload
        def __init__(self, func_spec: tuple[typing.Union[str, int], ctypes.CDLL], paramflags: typing.Optional[tuple[_PF, ...]] = ..., /) -> None: ...
        if os.name == "nt":
            @typing.overload
            def __init__(
                self, vtbl_index: int, name: str, paramflags: typing.Optional[tuple[_PF, ...]] = ..., iid: typing.Optional[_CData] = ..., /
            ) -> None: ...
        def __init__(self, *args, **kwargs): ...
        def __call__(self, *args: _PS.args, **kwds: _PS.kwargs) -> _PT:
            ...
else:
    class CFnType(typing.Generic[_PS, _PT]):
        def __new__(cls, rtype, *atypes, use_errno: bool = False, use_last_error: bool = True) -> type[_CFuncPtr]:
            atypes = _digest_annotated_types(*atypes)
            rtype, = _digest_annotated_types(rtype)
            return _create_cfunctype(rtype, *atypes, use_errno=use_errno, use_last_error=use_last_error)

        def __class_getitem__(cls, args: tuple[Sequence[type], type]) -> type[_CFuncPtr]:
            atypes, rtype = args
            atypes = _digest_annotated_types(*atypes)
            rtype, = _digest_annotated_types(rtype)
            return _create_cfunctype(rtype, *atypes)
        
        def __call__(self, *args: _PS.args, **kwds: _PS.kwargs) -> _PT:
            ...
