import sys


class ExactypesError(Exception): ...


class DeclarationError(ExactypesError): ...


class AnnotationError(DeclarationError):
    def __init__(self, message: str, target_name: str, key_name: str) -> None:
        if sys.version_info >= (3, 11):
            super().__init__(f"Error in parsing {key_name!r} of {target_name!r}")
            super().add_note(message)
        else:
            super().__init__(
                f"Error in parsing {key_name!r} of {target_name!r}:\n\t{message}"
            )


class ArrayError(ExactypesError): ...


class ArrayUntyped(ArrayError): ...
