import ctypes
import inspect
import sys
import types
import typing
from collections.abc import Sequence
from functools import partial

import typing_extensions

from ..exceptions import AnnotationError
from ..types import CT as _CT
from ..types import CData as _CData
from ..types import CDataObjectWrapper
from ..types import PyCPointerType as _PyCPointerType
from .datafield import CDataField as CDataField
from .refsolver import RefCache as RefCache
from .refsolver import get_unresolved_names

_CDO_T = typing.TypeVar("_CDO_T", ctypes.Structure, ctypes.Union)

if typing_extensions.TYPE_CHECKING:
    P: typing_extensions.TypeAlias = "ctypes._Pointer[_CT]"

    class _ExactCDOExtra(_CDO_T):  # type: ignore  # incredibly evil hack
        """Temporary annotation for custom fields, not exist in runtime."""
        _exactypes_unresolved_fields_: list[list]
        _fields_: Sequence[typing.Union[tuple[str, type[_CData]], tuple[str, type[_CData], int]]]
else:
    class P:
        def __new__(cls, cobj: typing.Union[_CT, _PyCPointerType, None] = None) -> "typing.Union[ctypes._Pointer[_CT], None]":
            if cobj is None:
                return None
            return ctypes.pointer(cobj)  # type: ignore

        def __class_getitem__(cls, pt: type[_CT]) -> type["ctypes._Pointer[_CT]"]:
            if isinstance(pt, str):
                return typing.cast(type["ctypes._Pointer[_CT]"], f"P[{pt!s}]")
            return typing.cast(type["ctypes._Pointer[_CT]"], ctypes.POINTER(pt))


# def _is_annotated(t: typing_extensions.Any) -> typing_extensions.TypeGuard[typing_extensions.Annotated]:
#     return isinstance(t, typing_extensions._AnnotatedAlias)  # pyright: ignore[reportAttributeAccessIssue]

_exactypes_cstruct_cache: RefCache = RefCache()


def _cdataobj(
    cls: typing.Optional[type[_CDO_T]] = None,
    /,
    *,
    pack: int = 0,
    align: int = 0,
    anonymous: typing.Optional[Sequence[str]] = None,
    ignpriv: bool = True,
    cachens: RefCache = _exactypes_cstruct_cache,
    frame: typing.Optional[types.FrameType] = None
) -> typing.Union[type[_CDO_T], CDataObjectWrapper[_CDO_T]]:
    if cls is None:
        return typing.cast(
            CDataObjectWrapper[_CDO_T], partial(_cdataobj, ignpriv=ignpriv, cachens=cachens, frame=frame)
        )  # take parameter and go

    cachens[cls.__name__] = cls

    cls._pack_ = pack
    if sys.version_info >= (3, 13):
        cls._align_ = align
    
    if anonymous is None:
        anonymous = []

    if frame is None:
        raise RuntimeError("cannot get context.")
    if (frame := frame.f_back) is None:
        raise RuntimeError("cannot get parent context.")

    if typing.TYPE_CHECKING:
        cls = typing.cast(_ExactCDOExtra, cls)  # the hack of _ExactCDOExtra used to solve it.
    cls._exactypes_unresolved_fields_ = []

    # for n, t in typing.get_type_hints(cls, None, _fr.f_locals | dict(cachens), include_extras=True).items():
    for n, t in (cls.__annotations__ or {}).items():
        if ignpriv and n.startswith("_"):
            continue

        if isinstance(t, str):
            if unresolved := get_unresolved_names(t, frame.f_globals, frame.f_locals, dict(cachens)):
                _field = [n, t]
                for name in unresolved:
                    cachens.listen(name, cls, _field, frame.f_globals, frame.f_locals)
                cls._exactypes_unresolved_fields_.append(_field)
                continue
            else:
                t = eval(t, frame.f_globals, frame.f_locals | dict(cachens))
                if isinstance(t, str):
                    t = eval(t, frame.f_globals, frame.f_locals | dict(cachens))

        if isinstance(t, (_CData, _PyCPointerType)):
            _field = [n, t]
            cls._exactypes_unresolved_fields_.append(_field)
            continue

        if not isinstance(t, (types.GenericAlias, typing._GenericAlias)):  # pyright: ignore[reportAttributeAccessIssue]
            raise AnnotationError(f"Bad annotation type '{t!s}'.")

        _type, *data = typing_extensions.get_args(t)
        _len = len(data)

        if _len < 1 or _len > 2:
            raise AnnotationError(f"Bad annotation type '{t!s}'.")

        if len(data) == 2:  # *, [CT, int]
            cls._exactypes_unresolved_fields_.append([n, *data])
            continue

        if (_orig := typing_extensions.get_origin(_type)) is not None and issubclass(_orig, CDataField):
            # [CDF[PT, CT], int]
            _, _type = typing.cast(tuple[object, _CData], typing_extensions.get_args(_type))
        elif not isinstance(_type, (str, _CData, _PyCPointerType)):  # PT, [CT]
            cls._exactypes_unresolved_fields_.append([n, *data])
            continue

        _field = [n, _type, *data]
        cls._exactypes_unresolved_fields_.append(_field)  # CT, [int]
        if isinstance(_type, str):  # str, [int]
            if unresolved := get_unresolved_names(_type, frame.f_globals, frame.f_locals, dict(cachens)):
                for name in unresolved:
                    cachens.listen(name, cls, _field, frame.f_globals, frame.f_locals)
            else:
                _field[1] = eval(_type, frame.f_globals, frame.f_locals | cachens)
                if isinstance(t, str):
                    _field[1] = eval(_field[1], frame.f_globals, frame.f_locals | cachens)

    if not any(isinstance(_tp, str) for _, _tp, *_ in cls._exactypes_unresolved_fields_) and getattr(cls, "_fields_", None) is None:
        cls._fields_ = tuple((n, tp, *data) for n, tp, *data in cls._exactypes_unresolved_fields_)

    return cls


@typing_extensions.overload
def cstruct(cls: type[ctypes.Structure], /) -> type[ctypes.Structure]:
    ...


@typing_extensions.overload
def cstruct(*, ignpriv: bool = True, cachens: RefCache = ...) -> CDataObjectWrapper[ctypes.Structure]:
    ...


@typing_extensions.dataclass_transform(field_specifiers=(CDataField,))
def cstruct(
    cls: typing.Optional[type[ctypes.Structure]] = None,
    /,
    *,
    pack: int = 0,
    align: int = 0,
    anonymous: Sequence[str] = (),
    ignpriv: bool = True,
    cachens: RefCache = _exactypes_cstruct_cache
) -> typing.Union[type[ctypes.Structure], CDataObjectWrapper[ctypes.Structure]]:
    return _cdataobj(cls, ignpriv=ignpriv, cachens=cachens, frame=inspect.currentframe())


@typing_extensions.overload
def cunion(cls: type[ctypes.Union], /) -> type[ctypes.Union]:
    ...


@typing_extensions.overload
def cunion(*, ignpriv: bool = True, cachens: RefCache = ...) -> CDataObjectWrapper[ctypes.Union]:
    ...


@typing_extensions.dataclass_transform(field_specifiers=(CDataField,))
def cunion(
    cls: typing.Optional[type[ctypes.Union]] = None,
    /,
    *,
    pack: int = 0,
    align: int = 0,
    anonymous: Sequence[str] = (),
    ignpriv: bool = True,
    cachens: RefCache = _exactypes_cstruct_cache
) -> typing.Union[type[ctypes.Union], CDataObjectWrapper[ctypes.Union]]:
    return _cdataobj(cls, ignpriv=ignpriv, cachens=cachens, frame=inspect.currentframe())