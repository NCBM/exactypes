from ctypes import c_int

from exactypes import array

a = array.of(c_int)(range(10), dynamic=True)

assert a[:] == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
del a[:2]
assert a[:] == [2, 3, 4, 5, 6, 7, 8, 9]
del a[1:4:2]
assert a[:] == [2, 4, 6, 7, 8, 9]
del a[-1]
assert a[:] == [2, 4, 6, 7, 8]
a.append(10)
assert a[:] == [2, 4, 6, 7, 8, 10]
a.extend(range(11, 21))
assert a[:] == [2, 4, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
a.remove(20)
assert a[:] == [2, 4, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
