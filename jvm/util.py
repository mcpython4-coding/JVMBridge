import struct
import jvm.api
import opcode

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


class PyOpcodes:
    POP_TOP = 1
    ROT_TWO = 2
    ROT_THREE = 3
    DUP_TOP = 4
    DUP_TOP_TWO = 5
    ROT_FOUR = 6

    NOP = 9
    UNARY_POSITIVE = 10
    UNARY_NEGATIVE = 11
    UNARY_NOT = 12

    UNARY_INVERT = 15

    BINARY_MATRIX_MULTIPLY = 16
    INPLACE_MATRIX_MULTIPLY = 17

    BINARY_POWER = 19
    BINARY_MULTIPLY = 20

    BINARY_MODULO = 22
    BINARY_ADD = 23
    BINARY_SUBTRACT = 24
    BINARY_SUBSCR = 25
    BINARY_FLOOR_DIVIDE = 26
    BINARY_TRUE_DIVIDE = 27
    INPLACE_FLOOR_DIVIDE = 28
    INPLACE_TRUE_DIVIDE = 29

    RERAISE = 48
    WITH_EXCEPT_START = 49
    GET_AITER = 50
    GET_ANEXT = 51
    BEFORE_ASYNC_WITH = 52

    END_ASYNC_FOR = 54
    INPLACE_ADD = 55
    INPLACE_SUBTRACT = 56
    INPLACE_MULTIPLY = 57

    INPLACE_MODULO = 59
    STORE_SUBSCR = 60
    DELETE_SUBSCR = 61
    BINARY_LSHIFT = 62
    BINARY_RSHIFT = 63
    BINARY_AND = 64
    BINARY_XOR = 65
    BINARY_OR = 66
    INPLACE_POWER = 67
    GET_ITER = 68
    GET_YIELD_FROM_ITER = 69

    PRINT_EXPR = 70
    LOAD_BUILD_CLASS = 71
    YIELD_FROM = 72
    GET_AWAITABLE = 73
    LOAD_ASSERTION_ERROR = 74
    INPLACE_LSHIFT = 75
    INPLACE_RSHIFT = 76
    INPLACE_AND = 77
    INPLACE_XOR = 78
    INPLACE_OR = 79

    LIST_TO_TUPLE = 82
    RETURN_VALUE = 83
    IMPORT_STAR = 84
    SETUP_ANNOTATIONS = 85
    YIELD_VALUE = 86
    POP_BLOCK = 87

    POP_EXCEPT = 89

    HAVE_ARGUMENT = 90  # Opcodes from here have an argument:

    STORE_NAME = 90  # Index in name list
    DELETE_NAME = 91  # ""
    UNPACK_SEQUENCE = 92  # Number of tuple items
    FOR_ITER = 93
    UNPACK_EX = 94
    STORE_ATTR = 95  # Index in name list
    DELETE_ATTR = 96  # ""
    STORE_GLOBAL = 97  # ""
    DELETE_GLOBAL = 98  # ""
    LOAD_CONST = 100  # Index in const list
    LOAD_NAME = 101  # Index in name list
    BUILD_TUPLE = 102  # Number of tuple items
    BUILD_LIST = 103  # Number of list items
    BUILD_SET = 104  # Number of set items
    BUILD_MAP = 105  # Number of dict entries
    LOAD_ATTR = 106  # Index in name list
    COMPARE_OP = 107  # Comparison operator
    IMPORT_NAME = 108  # Index in name list
    IMPORT_FROM = 109  # Index in name list

    JUMP_FORWARD = 110  # Number of bytes to skip
    JUMP_IF_FALSE_OR_POP = 111  # Target byte offset from beginning of code
    JUMP_IF_TRUE_OR_POP = 112  # ""
    JUMP_ABSOLUTE = 113  # ""
    POP_JUMP_IF_FALSE = 114  # ""
    POP_JUMP_IF_TRUE = 115  # ""

    LOAD_GLOBAL = 116  # Index in name list

    IS_OP = 117
    CONTAINS_OP = 118

    JUMP_IF_NOT_EXC_MATCH = 121
    SETUP_FINALLY = 122  # Distance to target address

    LOAD_FAST = 124  # Local variable number
    STORE_FAST = 125  # Local variable number
    DELETE_FAST = 126  # Local variable number

    RAISE_VARARGS = 130  # Number of raise arguments (1, 2, or 3)
    CALL_FUNCTION = 131  # #args
    MAKE_FUNCTION = 132  # Flags
    BUILD_SLICE = 133  # Number of items
    LOAD_CLOSURE = 135
    LOAD_DEREF = 136
    STORE_DEREF = 137
    DELETE_DEREF = 138

    CALL_FUNCTION_KW = 141  # #args + #kwargs
    CALL_FUNCTION_EX = 142  # Flags

    SETUP_WITH = 143

    LIST_APPEND = 145
    SET_ADD = 146
    MAP_ADD = 147

    LOAD_CLASSDEREF = 148

    EXTENDED_ARG = 144

    SETUP_ASYNC_WITH = 154

    FORMAT_VALUE = 155
    BUILD_CONST_KEY_MAP = 156
    BUILD_STRING = 157

    LOAD_METHOD = 160
    CALL_METHOD = 161

    LIST_EXTEND = 162
    SET_UPDATE = 163
    DICT_MERGE = 164
    DICT_UPDATE = 165

