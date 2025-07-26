import ast
import ctypes
import typing
from _ctypes import CFuncPtr as _CFuncPtr

from ..cfuncs import CCallWrapper
from . import std as std


def generate_stub(
    obj: typing.Union[_CFuncPtr, CCallWrapper, ctypes.Structure, ctypes.Union],
    style: typing.Literal["std"],
) -> str:
    if style == "std":
        stub_ast = std._generate_stub(obj)
    else:
        raise ValueError(f"unknown style: {style!r}")

    fixed_ast = ast.fix_missing_locations(stub_ast)
    return ast.unparse(fixed_ast)
