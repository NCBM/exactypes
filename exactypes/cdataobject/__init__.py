import ctypes
import inspect
import sys
import types
import typing
from collections.abc import Callable
from functools import partial, wraps

import typing_extensions

from ..exceptions import AnnotationError
from ..types import CTYPES, CDataObjectWrapper, CTypes, StructUnionType
from ..types import CData as _CData
from ..types import PyCPointerType as _PyCPointerType
from .datafield import CArrayField
from .datafield import CDataField as CDataField
from .refsolver import RefCache as RefCache
from .refsolver import get_unresolved_names

_CDO_T = typing.TypeVar("_CDO_T", ctypes.Structure, ctypes.Union)
_XCT = typing.TypeVar("_XCT", bound=CTypes)

if typing_extensions.TYPE_CHECKING:
    P: typing_extensions.TypeAlias = "ctypes._Pointer[_XCT]"
else:

    class P:
        def __new__(
            cls, cobj: typing.Union[_XCT, _PyCPointerType, None] = None
        ) -> "typing.Union[ctypes._Pointer[_XCT], None]":
            if cobj is None:
                return None
            return ctypes.pointer(cobj)  # type: ignore

        def __class_getitem__(cls, pt: type[_XCT]) -> type["ctypes._Pointer[_XCT]"]:
            if isinstance(pt, str):
                return typing.cast(type["ctypes._Pointer[_XCT]"], f"P[{pt!s}]")
            return typing.cast(type["ctypes._Pointer[_XCT]"], ctypes.POINTER(pt))


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


def _unwrap_classvar(
    cls: StructUnionType,
    frame: types.FrameType,
    real_fields: list[str],
    cachens: RefCache,
    name: str,
    tp: typing.Any,
):
    _field: list[typing.Any]
    if typing_extensions.get_origin(tp) is typing.ClassVar:
        # ClassVar[XXXXX] or ClassVar["XXXXX"], unwrap
        (tp,) = typing_extensions.get_args(tp)
    else:
        # assert isinstance(real_fields, list)
        real_fields.append(name)

    if isinstance(tp, str):  # "XXXXX", often from __future__.annotations
        if unresolved := get_unresolved_names(tp, frame.f_globals, frame.f_locals, dict(cachens)):
            _field = [name, tp]
            for name in unresolved:
                cachens.listen(name, cls, _field, real_fields, frame.f_globals, frame.f_locals)
            getattr(cls, "_exactypes_unresolved_fields_").append(_field)
            return str
        else:
            tp = eval(tp, frame.f_globals, frame.f_locals | dict(cachens))
            if isinstance(tp, str):  # P['XXXXX'] -> "P[XXXXX]"
                tp = eval(tp, frame.f_globals, frame.f_locals | dict(cachens))

    if typing_extensions.get_origin(tp) is typing.ClassVar:
        # ClassVar[XXXXX] from "ClassVar[XXXXX]"
        (tp,) = typing.get_args(tp)
        real_fields.remove(name)

    return tp


def _resolve_annotated_field(tp: typing.Any):  # noqa: C901
    args = typing_extensions.get_args(tp)  # unwrap generic args
    if len(args) == 3:  # [*, CT, int]
        _, _type, extra = typing.cast(tuple[typing.Any, type[CTypes], int], args)
        if not isinstance(extra, int):
            raise AnnotationError(
                f"The second annotation metadata must be an int, not {type(extra)}."
            )
        return _type, extra
    elif len(args) != 2:
        raise AnnotationError(f"Bad annotation type '{tp!s}'.")

    ptype_or_ctype, ctype_or_extra = args

    if not isinstance(ctype_or_extra, int):  # PT, CT
        return ctype_or_extra, None

    _type, extra = ptype_or_ctype, ctype_or_extra
    del ptype_or_ctype, ctype_or_extra

    origin = typing_extensions.get_origin(_type)
    if origin is None:  # CT?, int
        if not issubclass(_type, CTYPES):
            raise AnnotationError(f"Bad annotation type '{tp!s}'.")
        if issubclass(_type, ctypes.Array):
            raise AnnotationError(
                "Cannot apply int metadata on a untyped array or a typed and sized array."
            )
        return _type, extra

    if origin is ctypes.Array:  # Array[CT], int
        etype = typing.cast(type[CTypes], typing_extensions.get_args(_type)[0])
        return etype * extra, None

    if origin is CDataField:  # CDF[PT, CT], int
        _type = typing.cast(type[CTypes], typing_extensions.get_args(_type)[1])
        return _type, extra

    if origin is CArrayField:  # CAF[PT, CT], int
        etype = typing.cast(type[CTypes], typing_extensions.get_args(_type)[1])
        return etype * extra, None

    return _type, extra


def _resolve_field(  # noqa: C901
    cls: StructUnionType,
    frame: types.FrameType,
    real_fields: list[str],
    cachens: RefCache,
    name: str,
    tp: typing.Any,
):
    _field: list[typing.Any]
    tp = _unwrap_classvar(cls, frame, real_fields, cachens, name, tp)
    if tp is str:
        return

    # --- All ClassVar unwrapped ---

    origin = typing_extensions.get_origin(tp)

    if origin is None:  # non-generic, check whether tp is C type
        if issubclass(tp, (_CData, _PyCPointerType, ctypes.Structure, ctypes.Union, ctypes.Array)):
            _field = [name, tp]
            getattr(cls, "_exactypes_unresolved_fields_").append(_field)
            return
        raise AnnotationError(f"Bad annotation type '{tp!s}'.")

    if origin is ctypes.Array or origin is CArrayField:  # Array[CT] / CArrayField
        raise AnnotationError("Cannot use array type without length.")

    if origin is CDataField:  # CDF[PT, CT]
        _type = typing_extensions.get_args(tp)[1]

    _type, extra = _resolve_annotated_field(tp)

    if extra is None:
        _field = [name, _type]
    else:
        _field = [name, _type, extra]
    getattr(cls, "_exactypes_unresolved_fields_").append(_field)  # CT, [int]
    if isinstance(_type, str):  # str, [int]
        if unresolved := get_unresolved_names(
            _type, frame.f_globals, frame.f_locals, dict(cachens)
        ):
            for name in unresolved:
                cachens.listen(name, cls, _field, real_fields, frame.f_globals, frame.f_locals)
        else:
            _field[1] = eval(_type, frame.f_globals, frame.f_locals | cachens)
            if isinstance(tp, str):
                _field[1] = eval(_field[1], frame.f_globals, frame.f_locals | cachens)


def _cdataobj(
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
        # typeshed shipped with basedpyright (at least until v1.22.0) do not know this.
        cls._align_ = align  # pyright: ignore[reportAttributeAccessIssue]

    real_fields: list[str] = []

    if frame is None:
        raise RuntimeError("cannot get context.")
    if (frame := frame.f_back) is None:
        raise RuntimeError("cannot get parent context.")

    setattr(cls, "_exactypes_unresolved_fields_", [])  # noqa: B010
    # cls._exactypes_unresolved_fields_ = []

    for name, tp in (cls.__annotations__ or {}).items():
        _resolve_field(cls, frame, real_fields, cachens, name, tp)

    if defaults:
        _replace_init_defaults(cls, *((k, cls.__dict__.get(k, None)) for k in real_fields))
    else:
        _replace_init(cls, *real_fields)

    if (
        not any(
            isinstance(_tp, str) for _, _tp, *_ in getattr(cls, "_exactypes_unresolved_fields_")
        )
        and getattr(cls, "_fields_", None) is None
    ):
        cls._fields_ = tuple(
            (n, tp, *data) for n, tp, *data in getattr(cls, "_exactypes_unresolved_fields_")
        )
        delattr(cls, "_exactypes_unresolved_fields_")

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
