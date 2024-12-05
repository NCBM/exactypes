"""
This test checks whether the error message is expected.
"""
import ctypes
from typing import Annotated

from test_utils import assert_error

from exactypes.cdataobject import cstruct
from exactypes.exceptions import AnnotationError

with assert_error(
    AnnotationError,
    assert_message="Error in parsing 'a' of 'E1':\n\tBad annotation type '<class 'int'>'.",
):

    @cstruct
    class E1(ctypes.Structure):
        a: int


with assert_error(
    AnnotationError,
    assert_message=("Error in parsing 'a' of 'E2':\n" "\tCannot use array type without length."),
):

    @cstruct
    class E2(ctypes.Structure):
        a: ctypes.Array[ctypes.c_int]


with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing 'a' of 'E3':\n"
        "\tThe second annotation metadata must be an int, not <class 'str'>."
    ),
):

    @cstruct
    class E3(ctypes.Structure):
        a: Annotated[int, ctypes.c_int, "haha"]


with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing 'a' of 'E4':\n"
        "\tBad annotation type 'typing.Annotated[int, <class 'ctypes.c_int'>, 24, 'haha']'."
    ),
):

    @cstruct
    class E4(ctypes.Structure):
        a: Annotated[int, ctypes.c_int, 24, "haha"]


with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing 'a' of 'E5':\n\tBad annotation type 'typing.Annotated[int, 24]'."
    ),
):

    @cstruct
    class E5(ctypes.Structure):
        a: Annotated[int, 24]


with assert_error(
    AnnotationError,
    assert_message=(
        "Error in parsing 'a' of 'E6':\n"
        "\tCannot apply int metadata on a untyped array or a typed and sized array."
    ),
):

    @cstruct
    class E6(ctypes.Structure):
        a: Annotated[ctypes.Array, 24]
