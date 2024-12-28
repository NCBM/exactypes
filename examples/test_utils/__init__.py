import contextlib
import ctypes
import ctypes.util
import os
import sys
from collections.abc import Sequence
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
        assert_keywords: Optional[Sequence[str]] = None,
        fail_message: str = "",
        printexc: bool = False,
    ):
        self._exceptions = exceptions
        self._assert_keywords = (
            (assert_keywords,) if isinstance(assert_keywords, str) else assert_keywords
        )
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
            raise AssertionError(self._fail_message) from exc_value

        msg = str(exc_value) if exc_value is not None else None

        if exc_value is not None and sys.version_info >= (3, 11):
            if msg is None:
                msg = "\n".join(exc_value.__notes__)
            else:
                msg += "\n" + "\n".join(exc_value.__notes__)

        if (
            self._assert_keywords
            and msg is not None
            and any((kw not in msg) for kw in self._assert_keywords)
        ):
            raise AssertionError(self._fail_message) from exc_value

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
