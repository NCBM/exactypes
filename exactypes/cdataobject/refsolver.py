import ast
import typing
from functools import reduce
from operator import or_
from typing import Any
from weakref import WeakValueDictionary

import typing_extensions

from ..types import StructUnionType

# from typing import TypeVar

# T = TypeVar("T")


def get_unresolved_names(type_str: str, *namespaces: dict[str, Any]) -> set[str]:
    """
    Get the unresolved names from a type string.
    """

    names: set[str] = set()
    namespace: dict[str, Any] = reduce(or_, namespaces)

    for node in ast.walk(ast.parse(type_str)):
        if isinstance(node, ast.Name):
            _name = node.id
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            _name = node.value
        else:
            continue
        if _name in namespace:
            continue
        names.add(_name)

    return names


class RefCache(WeakValueDictionary[str, typing.Any]):
    """
    A weakref cache for resolving types.
    """

    _listening: dict[str, tuple[list, StructUnionType, tuple[dict[str, Any], ...], list[str]]]

    @typing_extensions.override
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._listening = {}

    @typing_extensions.override
    def __setitem__(self, key: str, value: typing.Any) -> None:
        super().__setitem__(key, value)
        if key not in self._listening:
            return
        target, orig, env, real_fields = self._listening[key]
        name, _type, *_ = typing.cast(tuple[str, str], target)
        if get_unresolved_names(_type, *env, dict(self)):
            return
        _env = reduce(or_, env)
        target[1] = eval(_type, _env, self)
        if isinstance(target[1], str):
            target[1] = eval(target[1], _env, self)
        if typing.get_origin(target[1]) is typing.ClassVar:
            (target[1],) = typing.get_args(target[1])
            real_fields.remove(name)
        if (
            not any(
                isinstance(_tp, str)
                for _, _tp, *_ in getattr(orig, "_exactypes_unresolved_fields_")
            )
            and getattr(orig, "_fields_", None) is None
        ):
            orig._fields_ = tuple(
                (n, tp, *data) for n, tp, *data in getattr(orig, "_exactypes_unresolved_fields_")
            )
            delattr(orig, "_exactypes_unresolved_fields_")
        del self._listening[key]

    def listen(
        self,
        name: str,
        orig: StructUnionType,
        target: list,
        real_fields: list[str],
        *namespaces: dict[str, Any],
    ) -> None:
        if name in self._listening:
            return
        self._listening[name] = target, orig, namespaces, real_fields
