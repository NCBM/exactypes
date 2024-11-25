from __future__ import annotations

import ctypes

from test_utils import assert_error, libc

from exactypes.cfuncs import CFnType, argtypes, ccall, restype
from exactypes.exceptions import AnnotationError

with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing '<parameter[2]>' of 'CFnType':\n\tBad annotation type '<class 'str'>'."
    ),
):
    E1 = CFnType[[argtypes.c_int, argtypes.c_char_p, str], restype.c_longdouble]

with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing '<return-type>' of 'CFnType':\n\tBad annotation type '<class 'float'>'."
    ),
):
    E2 = CFnType[[argtypes.c_int, argtypes.c_char_p], float]

with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing '<parameter[0]>' of 'strtod':\n\tBad annotation type '<class 'bytes'>'."
    ),
):

    @ccall(libc, override_name="strtod")
    def bytes_to_float(ss: bytes, se: argtypes.Pointer[ctypes.c_char_p]) -> restype.c_double: ...

with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing '<return-type>' of 'strtod':\n\tBad annotation type '<class 'float'>'."
    ),
):

    @ccall(libc, override_name="strtod")
    def bytes_to_float_1(ss: argtypes.c_char_p, se: argtypes.Pointer[ctypes.c_char_p]) -> float: ...
