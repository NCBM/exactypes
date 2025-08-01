# 预置 ctypes 字段类型到 (GetT, SetT) 的映射

PRESET_FIELD_TYPE_MAP = {
    "c_int": ("int", "int"),
    "c_uint": ("int", "int"),
    "c_short": ("int", "int"),
    "c_ushort": ("int", "int"),
    "c_long": ("int", "int"),
    "c_ulong": ("int", "int"),
    "c_longlong": ("int", "int"),
    "c_ulonglong": ("int", "int"),
    "c_float": ("float", "float"),
    "c_double": ("float", "float"),
    "c_longdouble": ("float", "float"),
    "c_byte": ("int", "int"),
    "c_ubyte": ("int", "int"),
    "c_char": ("bytes", "bytes"),
    "c_char_p": ("typing.Optional[bytes]", "typing.Optional[bytes]"),
    "c_void_p": ("int", "int"),
    "c_bool": ("bool", "bool"),
    "c_wchar": ("str", "str"),
    "c_wchar_p": ("typing.Optional[str]", "typing.Optional[str]"),
    "c_size_t": ("int", "int"),
    "c_ssize_t": ("int", "int"),
    "py_object": ("typing.Any", "typing.Any"),
}
