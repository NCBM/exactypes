from exactypes import array

a = array.of("c_wchar")("foo bar baz", dynamic=True)

assert a[:] == "foo bar baz"
a += "foo \n foo"
assert a[:] == "foo bar bazfoo \n foo"
