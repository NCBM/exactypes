from __future__ import annotations

import ctypes  # noqa: TC003  # actual type is required

from test_utils import assert_error, libc

from exactypes import argtypes as A
from exactypes import ccall
from exactypes import restype as R
from exactypes.cfuncs import CFnType
from exactypes.exceptions import AnnotationError

with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing '<parameter[2]>' of 'CFnType':\n\tBad annotation type '<class 'str'>'."
    ),
):
    E1 = CFnType[[A.c_int, A.c_char_p, str], R.c_longdouble]

with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing '<return-type>' of 'CFnType':\n\tBad annotation type '<class 'float'>'."
    ),
):
    E2 = CFnType[[A.c_int, A.c_char_p], float]

with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing '<parameter[0]>' of 'strtod':\n\tBad annotation type '<class 'bytes'>'."
    ),
):

    @ccall(libc, override_name="strtod")
    def bytes_to_float(ss: bytes, se: A.ArgPtr[ctypes.c_char_p]) -> R.c_double: ...

with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing '<return-type>' of 'strtod':\n\tBad annotation type '<class 'float'>'."
    ),
):

    @ccall(libc, override_name="strtod")
    def bytes_to_float_1(ss: A.c_char_p, se: A.ArgPtr[ctypes.c_char_p]) -> float: ...
