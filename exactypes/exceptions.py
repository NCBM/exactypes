class ExactypesError(Exception): ...


class PointerError(ExactypesError): ...


class DerefError(PointerError): ...


class DeclarationError(ExactypesError): ...


class AnnotationError(DeclarationError):
    def __init__(self, message: str, target_name: str, key_name: str) -> None:
        super().__init__(
            f"Error in parsing {key_name!r} of {target_name!r}:\n\t{message}"
        )


class ResolveError(DeclarationError): ...


class ArrayError(ExactypesError): ...


class ArrayUntyped(ArrayError): ...
