import ctypes
import inspect
import sys
import types
import typing
from collections.abc import Callable, Sequence
from functools import partial, wraps

import typing_extensions

from ..exceptions import AnnotationError
from ..types import CT as _CT
from ..types import CData as _CData
from ..types import CDataObjectWrapper, StructUnionType
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
        _anonymous_: Sequence[str]
else:

    class P:
        def __new__(
            cls, cobj: typing.Union[_CT, _PyCPointerType, None] = None
        ) -> "typing.Union[ctypes._Pointer[_CT], None]":
            if cobj is None:
                return None
            return ctypes.pointer(cobj)  # type: ignore

        def __class_getitem__(cls, pt: type[_CT]) -> type["ctypes._Pointer[_CT]"]:
            if isinstance(pt, str):
                return typing.cast(type["ctypes._Pointer[_CT]"], f"P[{pt!s}]")
            return typing.cast(type["ctypes._Pointer[_CT]"], ctypes.POINTER(pt))


_exactypes_cstruct_cache: RefCache = RefCache()


def _replace_init_defaults(cls: StructUnionType, *init_fields: tuple[str, typing.Any]) -> None:
    if not init_fields:
        return
    orig_init = cls.__init__
    _ns: dict[str, Callable[..., dict[str, typing.Any]]] = {}
    code = "".join(f"{k}={v}, " for k, v in init_fields)
    exec(
        "def _check_args("
        + code
        + "): return {k: v for k, v in locals().items() if v is not None}",
        _ns,
    )
    fn_check = _ns["_check_args"]

    @wraps(fn_check)
    def __init__(self, *args, **kwargs) -> None:
        orig_init(self, **fn_check(*args, **kwargs))

    cls.__init__ = __init__


def _replace_init(cls: StructUnionType, *init_fields: str) -> None:
    return _replace_init_defaults(cls, *((k, None) for k in init_fields))


def _cdataobj(  # noqa: C901
    cls: typing.Optional[type[_CDO_T]] = None,
    /,
    *,
    pack: int = 0,
    align: int = 0,
    defaults: bool = False,
    cachens: RefCache = _exactypes_cstruct_cache,
    frame: typing.Optional[types.FrameType] = None,
) -> typing.Union[type[_CDO_T], CDataObjectWrapper[_CDO_T]]:
    if cls is None:
        return typing.cast(
            CDataObjectWrapper[_CDO_T],
            partial(
                _cdataobj, pack=pack, align=align, defaults=defaults, cachens=cachens, frame=frame
            ),
        )  # take parameter and go

    cachens[cls.__name__] = cls

    cls._pack_ = pack
    if sys.version_info >= (3, 13):
        cls._align_ = align

    real_fields: list[str] = []

    if frame is None:
        raise RuntimeError("cannot get context.")
    if (frame := frame.f_back) is None:
        raise RuntimeError("cannot get parent context.")

    if typing.TYPE_CHECKING:
        cls = typing.cast(type[_ExactCDOExtra], cls)  # the hack of _ExactCDOExtra used to solve it.
    cls._exactypes_unresolved_fields_ = []  # type: ignore

    for n, t in (cls.__annotations__ or {}).items():
        _field: list[typing.Any]
        if typing.get_origin(t) is typing.ClassVar:
            (t,) = typing.get_args(t)
        else:
            assert isinstance(real_fields, list)
            real_fields.append(n)

        if isinstance(t, str):
            if unresolved := get_unresolved_names(
                t, frame.f_globals, frame.f_locals, dict(cachens)
            ):
                _field = [n, t]
                for name in unresolved:
                    cachens.listen(name, cls, _field, real_fields, frame.f_globals, frame.f_locals)
                cls._exactypes_unresolved_fields_.append(_field)
                continue
            else:
                t = eval(t, frame.f_globals, frame.f_locals | dict(cachens))
                if isinstance(t, str):
                    t = eval(t, frame.f_globals, frame.f_locals | dict(cachens))

        if typing.get_origin(t) is typing.ClassVar:
            (t,) = typing.get_args(t)
            real_fields.remove(n)

        if not isinstance(t, (types.GenericAlias, typing._GenericAlias)):  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]
            if issubclass(t, (_CData, _PyCPointerType, ctypes.Structure, ctypes.Union)):
                _field = [n, t]
                cls._exactypes_unresolved_fields_.append(_field)
                continue
            raise AnnotationError(f"Bad annotation type '{t!s}'.")

        _type, *data = typing_extensions.get_args(t)
        _len = len(data)

        if _len < 1 or _len > 2:
            raise AnnotationError(f"Bad annotation type '{t!s}'.")

        if len(data) == 2:  # *, [CT, int]
            cls._exactypes_unresolved_fields_.append([n, *data])
            continue

        if (_orig := typing_extensions.get_origin(_type)) is not None and issubclass(
            _orig, CDataField
        ):
            # [CDF[PT, CT], int]
            _, _type = typing.cast(tuple[object, _CData], typing_extensions.get_args(_type))
        elif not isinstance(_type, (str, _CData, _PyCPointerType)):  # PT, [CT]
            cls._exactypes_unresolved_fields_.append([n, *data])
            continue

        _field = [n, _type, *data]
        cls._exactypes_unresolved_fields_.append(_field)  # CT, [int]
        if isinstance(_type, str):  # str, [int]
            if unresolved := get_unresolved_names(
                _type, frame.f_globals, frame.f_locals, dict(cachens)
            ):
                for name in unresolved:
                    cachens.listen(name, cls, _field, real_fields, frame.f_globals, frame.f_locals)
            else:
                _field[1] = eval(_type, frame.f_globals, frame.f_locals | cachens)
                if isinstance(t, str):
                    _field[1] = eval(_field[1], frame.f_globals, frame.f_locals | cachens)

    if defaults:
        _replace_init_defaults(cls, *((k, cls.__dict__.get(k, None)) for k in real_fields))
    else:
        _replace_init(cls, *real_fields)

    if (
        not any(isinstance(_tp, str) for _, _tp, *_ in cls._exactypes_unresolved_fields_)
        and getattr(cls, "_fields_", None) is None
    ):
        cls._fields_ = tuple((n, tp, *data) for n, tp, *data in cls._exactypes_unresolved_fields_)
        del cls._exactypes_unresolved_fields_

    return cls


@typing_extensions.overload
def cstruct(cls: type[ctypes.Structure], /) -> type[ctypes.Structure]: ...


@typing_extensions.overload
def cstruct(
    *, pack: int = 0, align: int = 0, defaults: bool = False, cachens: RefCache = ...
) -> CDataObjectWrapper[ctypes.Structure]: ...


@typing_extensions.dataclass_transform()
def cstruct(
    cls: typing.Optional[type[ctypes.Structure]] = None,
    /,
    *,
    pack: int = 0,
    align: int = 0,
    defaults: bool = False,
    cachens: RefCache = _exactypes_cstruct_cache,
) -> typing.Union[type[ctypes.Structure], CDataObjectWrapper[ctypes.Structure]]:
    return _cdataobj(
        cls,
        pack=pack,
        align=align,
        defaults=defaults,
        cachens=cachens,
        frame=inspect.currentframe(),
    )


@typing_extensions.overload
def cunion(cls: type[ctypes.Union], /) -> type[ctypes.Union]: ...


@typing_extensions.overload
def cunion(
    *, pack: int = 0, align: int = 0, cachens: RefCache = ...
) -> CDataObjectWrapper[ctypes.Union]: ...


@typing_extensions.dataclass_transform(kw_only_default=True)
def cunion(
    cls: typing.Optional[type[ctypes.Union]] = None,
    /,
    *,
    pack: int = 0,
    align: int = 0,
    cachens: RefCache = _exactypes_cstruct_cache,
) -> typing.Union[type[ctypes.Union], CDataObjectWrapper[ctypes.Union]]:
    return _cdataobj(
        cls,
        pack=pack,
        align=align,
        defaults=False,
        cachens=cachens,
        frame=inspect.currentframe(),
    )
