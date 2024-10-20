import ctypes
import inspect
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
    if _cache is not None and (restype_, argtypes_, flags) in _cache:
        return _cache[(restype_, argtypes_, flags)]
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
    _PF: typing_extensions.TypeAlias = typing.Union[
        tuple[int], tuple[int, typing.Optional[str]], tuple[int, typing.Optional[str], typing.Any]
    ]
    _ECT: typing_extensions.TypeAlias = Callable[
        [typing.Optional[_CData], _CFuncPtr, tuple[_CData, ...]], _CData
    ]

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
        def __init__(
            self,
            func_spec: tuple[typing.Union[str, int], ctypes.CDLL],
            paramflags: typing.Optional[tuple[_PF, ...]] = ...,
            /,
        ) -> None: ...

        if os.name == "nt":

            @typing.overload
            def __init__(
                self,
                vtbl_index: int,
                name: str,
                paramflags: typing.Optional[tuple[_PF, ...]] = ...,
                iid: typing.Optional[_CData] = ...,
                /,
            ) -> None: ...

        def __init__(self, *args, **kwargs): ...
        def __call__(self, *args: _PS.args, **kwds: _PS.kwargs) -> _PT: ...
else:

    class CFnType(typing.Generic[_PS, _PT]):
        def __new__(
            cls, rtype, *atypes, use_errno: bool = False, use_last_error: bool = True
        ) -> type[_CFuncPtr]:
            atypes = _digest_annotated_types(*atypes)
            (rtype,) = _digest_annotated_types(rtype)
            return _create_cfunctype(
                rtype, *atypes, use_errno=use_errno, use_last_error=use_last_error
            )

        def __class_getitem__(cls, args: tuple[Sequence[type], type]) -> type[_CFuncPtr]:
            atypes, rtype = args
            atypes = _digest_annotated_types(*atypes)
            (rtype,) = _digest_annotated_types(rtype)
            return _create_cfunctype(rtype, *atypes)

        def __call__(self, *args: _PS.args, **kwds: _PS.kwargs) -> _PT: ...


class CCallWrapper(typing.Generic[_PS, _PT]):
    dll: ctypes.CDLL
    fnname: str
    argtypes: Sequence[type[CObjOrPtr]]
    restype: type[_PT]
    _paramorder: tuple[str, ...]
    _paramdefaults: dict[str, typing.Any]
    _hasvaargs: bool = False

    def __init__(
        self,
        dll: ctypes.CDLL,
        fn: Callable[_PS, _PT],
        _env: typing.Optional[types.FrameType] = None,
    ) -> None:
        self._solvefn(fn, _env)
        self.update(dll)

    def __call__(self, *args: _PS.args, **kwargs: _PS.kwargs) -> _PT:
        kwds = self._paramdefaults | kwargs
        kwds |= dict(zip(self._paramorder, args))
        _args = tuple(kwds[k] for k in self._paramorder)
        _vaargs = args[len(self._paramorder):]
        return self._func(*_args, *_vaargs)

    def _solvefn(
        self, fn: Callable[_PS, _PT], _env: typing.Optional[types.FrameType] = None
    ) -> None:
        sig = inspect.signature(fn)
        self.fnname = fn.__name__
        _argtypes: list[typing.Any] = []
        paramorder: list[str] = []
        self._paramdefaults = {}
        for k, p in sig.parameters.items():
            if p.kind == inspect.Parameter.VAR_POSITIONAL:
                self._hasvaargs = True
                continue
            paramorder.append(k)
            if p.annotation is inspect.Parameter.empty:
                raise TypeError(f"unannotated parameter {k!r}.")
            _argtypes.append(p.annotation)
            if p.default is not inspect.Parameter.empty:
                self._paramdefaults[k] = p.default
        self._paramorder = tuple(paramorder)
        _restype = sig.return_annotation
        if _env is not None:
            argtypes = _digest_annotated_types(
                *(
                    (eval(x, _env.f_globals, _env.f_locals) if isinstance(x, str) else x)
                    for x in _argtypes
                )
            )
            self.argtypes = argtypes

            (_restype,) = _digest_annotated_types(
                eval(_restype, _env.f_globals, _env.f_locals)
                if isinstance(_restype, str)
                else _restype
            )
        else:
            self.argtypes = _argtypes
        self.restype = typing.cast(type[_PT], _restype)

    def update(self, dll: ctypes.CDLL) -> None:
        self.dll = dll
        self._func = self.dll[self.fnname]
        self._func.argtypes = self.argtypes
        self._func.restype = self.restype


def ccall(lib: ctypes.CDLL, *, override_name: typing.Optional[str] = None):
    frame = inspect.currentframe()
    if frame is not None:
        frame = frame.f_back

    def _ccall(fn: Callable[_PS, _PT]) -> CCallWrapper[_PS, _PT]:
        if override_name is not None:
            fn.__name__ = override_name
        return CCallWrapper(lib, fn, frame)

    return _ccall
