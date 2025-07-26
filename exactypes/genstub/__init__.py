import ast
from typing import Literal

from . import std as std


def generate_stub(obj, style: Literal["std"]) -> str:
    if style == "std":
        stub_ast = std._generate_stub(obj)
    else:
        raise ValueError(f"unknown style: {style!r}")

    fixed_ast = ast.fix_missing_locations(stub_ast)
    return ast.unparse(fixed_ast)
