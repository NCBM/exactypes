"""
Generate .pyi type stubs in standard format.

input(1): somelib.symname { .argtypes = [...], .restype = R }
input(2): CCallWrapper[..., R](fn)  # annotated with exactypes pattern
output: def fn(...) -> R: ...  # types should be expanded

input: class CXxx(ctypes.Structure): ...  # or ctypes.Union, with fields declaration, with or without exactypes pattern
output:
>>> class CXxx(ctypes.Structure):  # or ctypes.Union
...     field_1: _ctypes._CField[_CT, _GetT, _SetT]
...     ...
...
"""

import ast
import ctypes
import typing
from _ctypes import CFuncPtr as _CFuncPtr

from ..cfuncs import CCallWrapper


def _generate_stub(
    obj: typing.Union[_CFuncPtr, CCallWrapper, ctypes.Structure, ctypes.Union],
) -> ast.stmt:
    """
    Generate type stubs for the given object.

    :param obj: The object to generate stubs for. Can be a ctypes function pointer, CCallWrapper,
                ctypes.Structure, or ctypes.Union.
    :return: An AST statement representing the type stub.
    """

    if isinstance(obj, _CFuncPtr):
        # Handle ctypes function pointers
        argtypes = getattr(obj, "_argtypes_", [])
        restype = getattr(obj, "_restype_", None)
        args = [
            ast.arg(arg=f"arg{i}", annotation=ast.Name(id=arg.__name__))
            for i, arg in enumerate(argtypes)
        ]
        return ast.FunctionDef(
            name=getattr(obj, "__name__"),
            args=ast.arguments(
                posonlyargs=[],
                args=args,
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=[ast.Expr(value=ast.Constant(value=Ellipsis))],
            decorator_list=[],
            returns=ast.Name(id=restype.__name__ if restype else "None"),
        )

    elif isinstance(obj, CCallWrapper):
        # Handle CCallWrapper
        argtypes = obj.argtypes
        restype = obj.restype
        args = [
            ast.arg(arg=name, annotation=ast.Name(id=type_.__name__))
            for name, type_ in zip(obj._paramorder, argtypes)
        ]
        return ast.FunctionDef(
            name=obj._original_name,
            args=ast.arguments(
                posonlyargs=[],
                args=args,
                vararg=ast.arg(arg="args") if obj._hasvaargs else None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=[ast.Expr(value=ast.Constant(value=Ellipsis))],
            decorator_list=[],
            returns=ast.Name(id=restype.__name__),
        )

    elif isinstance(obj, (ctypes.Structure, ctypes.Union)):
        # Handle ctypes.Structure and ctypes.Union
        fields = getattr(obj, "_fields_", [])
        base_name = obj.__class__.__bases__[0].__name__

        from ._preset_field_types import PRESET_FIELD_TYPE_MAP

        class_body: list[ast.stmt] = []
        for name, type_ in fields:
            ctype_name = type_.__name__
            get_t, set_t = PRESET_FIELD_TYPE_MAP.get(ctype_name, ("typing.Any", "typing.Any"))

            def _get_builtin_type(type_str):
                if type_str in {"int", "float", "str", "bool", "bytes", "None"}:
                    return ast.Name(id=type_str)
                return ast.Name(id=type_str)

            def _set_union_type(type_str, ctype_name):
                if type_str in {"int", "float", "str", "bool", "bytes", "None"}:
                    return ast.Subscript(
                        value=ast.Name(id="Union"),
                        slice=ast.Tuple(
                            elts=[ast.Name(id=type_str), ast.Name(id=ctype_name)],
                            ctx=ast.Load(),
                        ),
                        ctx=ast.Load(),
                    )
                # 复杂类型如 Optional[...] 直接 parse
                if "[" in type_str:
                    return ast.parse(type_str, mode="eval").body
                return ast.Name(id=type_str)

            class_body.append(
                ast.AnnAssign(
                    target=ast.Name(id=name),
                    annotation=ast.Subscript(
                        value=ast.Attribute(value=ast.Name(id="_ctypes"), attr="_CField"),
                        slice=ast.Tuple(
                            elts=[
                                ast.Name(id=ctype_name),
                                _get_builtin_type(get_t),
                                _set_union_type(set_t, ctype_name),
                            ],
                            ctx=ast.Load(),
                        ),
                        ctx=ast.Load(),
                    ),
                    value=ast.Constant(value=Ellipsis),
                    simple=1,
                )
            )
        return ast.ClassDef(
            name=obj.__class__.__name__,
            bases=[ast.Attribute(value=ast.Name(id="ctypes"), attr=base_name)],
            keywords=[],
            body=class_body,
            decorator_list=[ast.Name(id="dataclass")],
        )

    else:
        raise TypeError(f"Unsupported type for stub generation: {type(obj)}")


def generate_stub(
    obj: typing.Union[_CFuncPtr, CCallWrapper, ctypes.Structure, ctypes.Union],
) -> str:
    """
    Generate type stubs for the given object and return as a string.

    :param obj: The object to generate stubs for.
    :return: A string representation of the type stub.
    """
    stub_ast = _generate_stub(obj)
    fixed_ast = ast.fix_missing_locations(stub_ast)
    return ast.unparse(fixed_ast)
