import struct
import jvm.api

U1 = struct.Struct("!B")
U1_S = struct.Struct("!b")
U1_S_4 = struct.Struct("!bbbb")
U2 = struct.Struct("!H")
U2_S = struct.Struct(">h")
U4 = struct.Struct("!I")
U4_S = struct.Struct(">i")
INT = struct.Struct("!i")
FLOAT = struct.Struct("!f")
LONG = struct.Struct("!q")
DOUBLE = struct.Struct("!d")


def pop_u1(data: bytearray):
    e = data[:1]
    del data[0]
    return U1.unpack(e)[0]


def pop_u2_s(data: bytearray):
    e = data[:2]
    del data[:2]
    return U2_S.unpack(e)[0]


def pop_u2(data: bytearray):
    e = data[:2]
    del data[:2]
    return U2.unpack(e)[0]


def pop_u4(data: bytearray) -> int:
    e = data[:4]
    del data[:4]
    return U4.unpack(e)[0]


def pop_u4_s(data: bytearray):
    e = data[:4]
    del data[:4]
    return U4_S.unpack(e)[0]


def pop_sized(size: int, data: bytearray):
    e = data[:size]
    del data[:size]
    return bytes(e)


def pop_struct(s: struct.Struct, data: bytearray):
    return s.unpack(pop_sized(s.size, data))


def decode_cp_constant(const, version=0):
    """
    Helper code for decoding an arbitrary constant pool entry down to a "primitive"
    Used in the instructions directly loading from the runtime constant pool and storing the stuff
    in the runtime.
    :param const: the const, as stored in the constant pool
    :param version: the internal version of the class system, to use when loading a class
    :return: the primitive
    :raises NotImplementedError: when the constant pool entry could not be decoded with this decoded
    """

    if const[0] == 7:  # Class
        return jvm.api.vm.get_class(const[1][1], version=version)
    elif const[0] in (1, 3, 4, 5, 6, 8):
        return const[1][1] if isinstance(const[1], list) else const[1]
    raise NotImplementedError(const)