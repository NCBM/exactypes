# exactypes

Helps creating typed ctypes-based python library.

Code examples can be found in [examples](./examples/).

## Installation

Use `pip` or whatever package/project managers to install:

```shell
pip install exactypes
```

## Features

### Better typing support for functions

Defining external functions more conveniently with annotations.

```python
>>> from exactypes import ccall, argtypes as A, restype as R
>>> from ctypes import CDLL
>>> libc = CDLL("libc.so.6")  # find your own library
>>> @ccall(libc)
... def printf(fmt: A.c_char_p, *args: A.VaArgs) -> R.c_int:
...     pass
... 
>>> printf("The answer is %d.\n", 42)
The answer is 42.
18
```

### Better typing support for structures and unions

Defining structures and/or unions like dataclasses.

```python
>>> import ctypes
>>> import typing
>>> from exactypes import Ptr, cstruct
>>> from exactypes import datafield as D
>>> IntArr_8 = typing.Annotated[D.array_of("c_int"), 8]
>>> @cstruct
... class Example(ctypes.Structure):
...     a: D.c_int = D.value()
...     _padding: typing.ClassVar[D.c_int]
...     b: D.c_double = D.value()
...     m: Ptr["Example"] = D.value()
...     n: IntArr_8 = D.value()
... 
>>> a = Example(123, 246, Ptr())
>>> a.m = Ptr(a)
>>> a.m.contents.m.contents.b
246.0
>>> a.n[:]
[0, 0, 0, 0, 0, 0, 0, 0]
```

### Maybe worse array interface?

Playing with arrays.

```python
>>> from exactypes.hazmat import array
>>> a = array.of("c_int")(range(10))
>>> a[:]
[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
```
