from ctypes import c_int

from exactypes import array

# written in the stage of preliminary development, use c_int wrapper to make type checker(s) happy.
a = array.Array[c_int]([c_int(i) for i in range(10)], dynamic=True)

assert [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] == a[:]
del a[:2]
assert [2, 3, 4, 5, 6, 7, 8, 9] == a[:]
del a[1:4:2]
assert [2, 4, 6, 7, 8, 9] == a[:]
del a[-1]
assert [2, 4, 6, 7, 8] == a[:]
a.append(c_int(10))
assert [2, 4, 6, 7, 8, 10] == a[:]
a.extend(c_int(i) for i in range(11, 21))
assert [2, 4, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20] == a[:]
