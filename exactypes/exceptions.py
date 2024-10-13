class ExactypesError(Exception): ...


class PointerError(ExactypesError): ...


class DerefError(PointerError): ...


class DeclarationError(ExactypesError): ...


class AnnotationError(DeclarationError): ...


class ResolveError(DeclarationError): ...