import os

from . import argtypes as argtypes
from . import cfunc as cfunc
from . import restype as restype
from .cfunc import CCallWrapper as CCallWrapper
from .cfunc import CFnType as CFnType
from .cfunc import ccall as ccall

if os.name == "nt":
    from .cfunc import WinFnType as WinFnType
