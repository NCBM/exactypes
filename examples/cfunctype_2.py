import ctypes

from exactypes.cfuncs import argtypes, ccall, restype


@ccall(ctypes.CDLL("libc.so.6"))
def printf(fmt: argtypes.c_char_p, *args: argtypes.VaArgs) -> restype.c_int:
    ...


out1 = printf(b"Hello, %s!\n", b"World")
out2 = printf(b"The price of this shirt is %.2f.\n", ctypes.c_double(9.15))
out3 = printf(b"(%d, %d, %d)\n", 178, 116, 339)

assert out1 == 14
assert out2 == 33
assert out3 == 16
