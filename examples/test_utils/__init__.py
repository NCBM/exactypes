import contextlib
import ctypes
import ctypes.util
import os
from types import TracebackType
from typing import Literal, Optional


class assert_error(contextlib.AbstractContextManager):
    """Context manager to assert specified exceptions

    Only when the specified exceptions are caught, they will be suppressed,
    otherwise raise uncaught errors and/or AssertionError.

        >>> with assert_error(FileNotFoundError):
        >>>     os.remove(somefile)
        >>> # Execution resumes here unless no specified exceptions raised.
    """

    def __init__(
        self,
        *exceptions,
        assert_message: Optional[str] = None,
        fail_message: str = "",
        printexc: bool = False,
    ):
        self._exceptions = exceptions
        self._assert_message = assert_message
        self._fail_message = fail_message
        self._printexc = printexc

    def __enter__(self):
        pass

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
        /,
    ) -> Literal[True]:
        if exc_type is None or not issubclass(exc_type, self._exceptions):
            raise AssertionError(self._fail_message)

        msg = str(exc_value) if exc_value is not None else None

        if self._assert_message is not None and msg != self._assert_message:
            raise AssertionError(self._fail_message)

        if self._printexc:
            if msg:
                print(f"{exc_type.__name__}:", str(exc_value))
            else:
                print(exc_type.__name__)
        return True


if os.name == "nt":
    libc = ctypes.CDLL("msvcrt")
else:
    libc = ctypes.CDLL(ctypes.util.find_library("c"))
