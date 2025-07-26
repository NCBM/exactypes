import ctypes

from test_utils import libc

from exactypes import cstruct, cunion
from exactypes import datafield as D
from exactypes.cfuncs import argtypes as A
from exactypes.cfuncs import ccall
from exactypes.cfuncs import restype as R
from exactypes.genstub.std import generate_stub


@cstruct()
class DemoStruct(ctypes.Structure):
    a: D.c_int = D.value()
    b: D.c_double = D.value()


@cunion()
class DemoUnion(ctypes.Union):
    x: D.c_int = D.value()
    y: D.c_float = D.value()


libc_func = libc.abs
libc_func.argtypes = [ctypes.c_int]
libc_func.restype = ctypes.c_int


@ccall(libc, override_name="abs")
def abs_func(x: A.c_int) -> R.c_int: ...


@ccall(libc)
def printf(fmt: A.c_char_p, *args: A.VaArgs) -> R.c_int: ...


# 输出
print("# ---Struct---", generate_stub(DemoStruct()), sep="\n\n", end="\n\n")
print("# ---Union---", generate_stub(DemoUnion()), sep="\n\n", end="\n\n")
# print("# ---CFuncPtr---", generate_stub(libc_func), sep="\n\n", end="\n\n")
print("# ---CCallWrapper---", generate_stub(abs_func), generate_stub(printf), sep="\n\n", end="\n\n")
