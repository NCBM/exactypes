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
    from _ctypes import FUNCFLAG_STDCALL as _FUNCFLAG_STDCALL

import types

import typing_extensions

from ..exceptions import AnnotationError

# from ..types import CT as _CT
from ..types import CTYPES, CDataType
from ..types import CData as _CData
from . import argtypes as argtypes
from . import restype as restype

_PS = typing_extensions.ParamSpec("_PS")
_PT = typing_extensions.TypeVar("_PT")
_IPT = typing_extensions.TypeVar("_IPT")


if typing.TYPE_CHECKING:

    @typing.type_check_only
    class CFunctionType(_CFuncPtr): ...

    if os.name == "nt":

        @typing.type_check_only
        class WinFunctionType(_CFuncPtr): ...


_FunctionType: typing_extensions.TypeAlias = typing.Union[
    type["CFunctionType"], type["WinFunctionType"]
]


@typing_extensions.overload
def _create_functype(
    name: typing_extensions.Literal["CFunctionType"],
    restype_: type[CDataType],
    *argtypes_: type[CDataType],
    flags: int,
    _cache: typing.Optional[
        dict[tuple[type[CDataType], tuple[type[CDataType], ...], int], type["CFunctionType"]]
    ],
) -> type["CFunctionType"]: ...


@typing_extensions.overload
def _create_functype(
    name: typing_extensions.Literal["WinFunctionType"],
    restype_: type[CDataType],
    *argtypes_: type[CDataType],
    flags: int,
    _cache: typing.Optional[
        dict[tuple[type[CDataType], tuple[type[CDataType], ...], int], type["WinFunctionType"]]
    ],
) -> type["WinFunctionType"]: ...


def _create_functype(
    name: typing_extensions.Literal["CFunctionType", "WinFunctionType"],
    restype_: type[CDataType],
    *argtypes_: type[CDataType],
    flags: int,
    _cache: typing.Union[
        dict[tuple[type[CDataType], tuple[type[CDataType], ...], int], type["CFunctionType"]],
        dict[tuple[type[CDataType], tuple[type[CDataType], ...], int], type["WinFunctionType"]],
        None,
    ],
) -> _FunctionType:
    if _cache is not None and (restype_, argtypes_, flags) in _cache:
        return _cache[(restype_, argtypes_, flags)]
    _type = type(
        name, (_CFuncPtr,), {"_argtypes_": argtypes_, "_restype_": restype_, "_flags_": flags}
    )
    if _cache is not None:
        _cache[(restype_, argtypes_, flags)] = _type
    return _type


def _create_cfunctype(
    restype_: type[CDataType],
    *argtypes_: type[CDataType],
    use_errno: bool = False,
    use_last_error: bool = False,
) -> type["CFunctionType"]:
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
        restype_: type[CDataType],
        *argtypes_: type[CDataType],
        use_errno: bool = False,
        use_last_error: bool = False,
    ) -> type["WinFunctionType"]:
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
        restype_: type[CDataType],
        *argtypes_: type[CDataType],
        use_errno: bool = False,
        use_last_error: bool = False,
    ) -> typing_extensions.Never:
        raise RuntimeError("`WinFunctionType` can only be created on Windows platform.")


def _create_pyfunctype(
    restype_: type[CDataType], *argtypes_: type[CDataType]
) -> type["CFunctionType"]:
    flags = _FUNCFLAG_CDECL | _FUNCFLAG_PYTHONAPI
    return _create_functype("CFunctionType", restype_, *argtypes_, flags=flags, _cache=None)


def _digest_annotated_types(
    *types_: type, target_name: str, key_name: typing.Optional[str] = None
) -> tuple[type[CDataType], ...]:
    res: list[type[CDataType]] = []
    for i, tp in enumerate(types_):
        if typing_extensions.get_origin(tp) is not None:
            _, tp = typing.cast(tuple[typing.Any, type], typing_extensions.get_args(tp))

        if issubclass(tp, CTYPES):
            res.append(tp)  # pyright: ignore[reportArgumentType] # feel free to put data, it's safe
            continue

        if not issubclass(tp, CTYPES):
            raise AnnotationError(
                f"Bad annotation type '{tp!s}'.",
                target_name,
                key_name if key_name is not None else f"<parameter[{i}]>",
            )

        res.append(tp)  # pyright: ignore[reportArgumentType] # see above
    return tuple(res)


if typing.TYPE_CHECKING:
    _PF: typing_extensions.TypeAlias = typing.Union[
        tuple[int], tuple[int, typing.Optional[str]], tuple[int, typing.Optional[str], typing.Any]
    ]

    class CFnType(_CFuncPtr, typing.Generic[_PS, _PT]):
        """
        Wrapper for `CFUNCTYPE`.

        Create a CFunctionType with:

        >>> CFnType[[argtype1, argtype2, ...], restype]
        """

        _restype_: typing.Union[type[CDataType], Callable[[int], typing.Any], None]
        _argtypes_: Sequence[type[CDataType]]
        _errcheck_: Callable[
            [
                typing.Union[_CData, CDataType, None],
                _CFuncPtr,
                tuple[typing.Union[_CData, CDataType], ...],
            ],
            CDataType,
        ]
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
        """
        Wrapper for `CFUNCTYPE`.

        Create a CFunctionType with:

        >>> CFnType[[argtype1, argtype2, ...], restype]
        """

        def __new__(
            cls, rtype, *atypes, use_errno: bool = False, use_last_error: bool = True
        ) -> type[_CFuncPtr]:
            atypes = _digest_annotated_types(*atypes)
            if rtype == "None":
                rtype = None
            if rtype is not None:
                (rtype,) = _digest_annotated_types(rtype)
            return _create_cfunctype(
                rtype, *atypes, use_errno=use_errno, use_last_error=use_last_error
            )

        def __class_getitem__(cls, args: tuple[Sequence[type], type]) -> type[_CFuncPtr]:
            atypes, rtype = args
            atypes = _digest_annotated_types(*atypes, target_name=cls.__name__)
            if rtype == "None":
                rtype = None
            if rtype is not None:
                (rtype,) = _digest_annotated_types(
                    rtype,
                    target_name=cls.__name__,
                    key_name="<return-type>",
                )
            return _create_cfunctype(rtype, *atypes)

        def __call__(self, *args: _PS.args, **kwds: _PS.kwargs) -> _PT: ...


class CCallWrapper(typing.Generic[_PS, _PT]):
    """
    A wrapper for python callables annotated with ctypes types.

    This class is used to wrap C functions with python functions annotated with ctypes types.
    The wrapped callable can be called as if it were a normal python function.
    """

    dll: ctypes.CDLL
    fnname: str
    argtypes: Sequence[type[CDataType]]
    restype: type[_PT]
    _paramorder: tuple[str, ...]
    _paramdefaults: dict[str, typing.Any]
    _hasvaargs: bool = False
    _errcheck: typing.Optional[
        Callable[
            [
                typing.Union[_CData, CDataType, None],
                _CFuncPtr,
                tuple[typing.Union[_CData, CDataType], ...],
            ],
            _PT,
        ]
    ] = None

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
        _vaargs = args[len(self._paramorder) :]
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
                ),
                target_name=self.fnname,
            )
            self.argtypes = argtypes

            if _restype == "None":
                _restype = None
            if _restype is not None:
                (_restype,) = _digest_annotated_types(
                    eval(_restype, _env.f_globals, _env.f_locals)
                    if isinstance(_restype, str)
                    else _restype,
                    target_name=self.fnname,
                    key_name="<return-type>",
                )
        else:
            self.argtypes = _argtypes
        self.restype = typing.cast(type[_PT], _restype)

    def update(self, dll: ctypes.CDLL) -> None:
        self.dll = dll
        self._func = self.dll[self.fnname]
        self._func.argtypes = self.argtypes
        self._func.restype = self.restype
        if self._errcheck is not None:
            self._func.errcheck = self._errcheck  # pyright: ignore[reportAttributeAccessIssue]

    def as_cfntype(self) -> type["CFnType[_PS, _PT]"]:
        if typing.TYPE_CHECKING:
            return CFnType[_PS, _PT]
        return CFnType[[*self.argtypes], self.restype]

    def errcheck(
        self,
        ecf: Callable[
            [
                _PT,
                _CFuncPtr,
                tuple[typing.Union[_CData, CDataType], ...],
            ],
            _IPT,
        ],
    ) -> "CCallWrapper[_PS, _IPT]":
        # here we change the return type both runtime and typing.
        # doing this requires many ignore comments.
        self._func.errcheck = ecf  # pyright: ignore[reportAttributeAccessIssue]
        self._errcheck = ecf  # pyright: ignore[reportAttributeAccessIssue]
        return self  # pyright: ignore[reportReturnType]


def ccall(lib: ctypes.CDLL, *, override_name: typing.Optional[str] = None):
    """
    Decorator for wrapping a ctypes function.

    :param lib: The ctypes library including the function you want to wrap.

    :param override_name: Override the name of the wrapped function. If `None`, use the decorated \
                          function's name.
    """
    frame = inspect.currentframe()
    if frame is not None:
        frame = frame.f_back

    def _ccall(fn: Callable[_PS, _PT]) -> CCallWrapper[_PS, _PT]:
        """
        Wrap a python function.

        :param fn: The function to wrap.
        """
        if override_name is not None:
            fn.__name__ = override_name
        return CCallWrapper(lib, fn, frame)

    return _ccall
