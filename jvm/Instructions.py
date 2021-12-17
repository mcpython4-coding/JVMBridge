import array
import copy
import dis
import typing
from abc import ABC

from mcpython.mixin.util import PyOpcodes

import jvm.Java
import jvm.util
from jvm.api import BaseInstruction, AbstractRuntime, AbstractBytecodeContainer, AbstractStack
from jvm.api import PyBytecodeBuilder
from jvm.JavaExceptionStack import StackCollectingException


class OpcodeInstruction(BaseInstruction, ABC):
    """
    Base for an opcode based instruction
    """

    OPCODES: typing.Set[int] = set()

    @classmethod
    def decode(
            cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return None, 1


class CPLinkedInstruction(OpcodeInstruction, ABC):
    """
    Base class for instructions containing one single constant pool reference
    Used often in instructions
    """

    @classmethod
    def decode(
            cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        pointer = jvm.util.U2.unpack(data[index: index + 2])[0] - 1
        try:
            return (
                class_file.cp[pointer],
                3,
            )
        except IndexError:
            raise StackCollectingException(
                f"during decoding instruction {cls.__name__} pointing to {pointer}"
            ).add_trace(f"current parsing index: {index}, class: {class_file.name}")


@AbstractBytecodeContainer.register_instruction
class NoOp(OpcodeInstruction):
    # NoOp
    OPCODES = {0x00}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack) -> bool:
        pass

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.NOP)


@AbstractBytecodeContainer.register_instruction
class NoOpPop(OpcodeInstruction):
    # C2 and C3: monitor stuff, as we are not threading, this works as it is
    OPCODES = {0xC2, 0xC3}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.pop()

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        
    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.POP_TOP)


@AbstractBytecodeContainer.register_instruction
class Any2Byte(OpcodeInstruction):
    # i2b
    OPCODES = {0x91}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        v = stack.pop()
        stack.push(int(v) if v is not None else v)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.push("B")

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_NAME, builder.add_name("bytes"))
        builder.add_instruction(PyOpcodes.ROT_TWO)
        builder.add_instruction(PyOpcodes.BUILD_LIST, 1)
        builder.add_instruction(PyOpcodes.CALL_FUNCTION, 1)


@AbstractBytecodeContainer.register_instruction
class Any2Float(OpcodeInstruction):
    # i2f, d2f
    OPCODES = {0x86, 0x90}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        v = stack.pop()
        stack.push(float(v) if v is not None else v)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.push("F")

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_NAME, builder.add_name("float"))
        builder.add_instruction(PyOpcodes.ROT_TWO)
        builder.add_instruction(PyOpcodes.CALL_FUNCTION, 1)


@AbstractBytecodeContainer.register_instruction
class Any2Double(Any2Float):
    # i2d, f2d, l2d
    OPCODES = {0x87, 0x8D, 0x8A}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.push("D")

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_NAME, builder.add_name("float"))
        builder.add_instruction(PyOpcodes.ROT_TWO)
        builder.add_instruction(PyOpcodes.CALL_FUNCTION, 1)


@AbstractBytecodeContainer.register_instruction
class Any2Int(OpcodeInstruction):
    # d2i, f2i, l2i
    OPCODES = {0x8E, 0x8B, 0x88}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        v = stack.pop()
        stack.push(int(v) if v is not None else v)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.push("I")

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_NAME, builder.add_name("int"))
        builder.add_instruction(PyOpcodes.ROT_TWO)
        builder.add_instruction(PyOpcodes.CALL_FUNCTION, 1)


@AbstractBytecodeContainer.register_instruction
class Any2Long(Any2Int):
    # f2l
    OPCODES = {0x8C, 0x85, 0x8F}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.push("J")

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_NAME, builder.add_name("int"))
        builder.add_instruction(PyOpcodes.ROT_TWO)
        builder.add_instruction(PyOpcodes.CALL_FUNCTION, 1)


class ConstPush(OpcodeInstruction, ABC):
    """
    Base class for instructions pushing pre-defined objects
    """

    PUSHES = None
    PUSH_TYPE = None

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push(cls.PUSHES)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.push(cls.PUSH_TYPE)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_CONST, builder.add_const(cls.PUSHES))


@AbstractBytecodeContainer.register_instruction
class AConstNull(ConstPush):
    OPCODES = {0x01}
    PUSH_TYPE = "null"


@AbstractBytecodeContainer.register_instruction
class IConstM1(ConstPush):
    OPCODES = {0x02}
    PUSHES = -1
    PUSH_TYPE = "i"


@AbstractBytecodeContainer.register_instruction
class IConst0(ConstPush):
    OPCODES = {0x03}
    PUSHES = 0
    PUSH_TYPE = "i"


@AbstractBytecodeContainer.register_instruction
class LConst0(ConstPush):
    OPCODES = {0x09}
    PUSHES = 0
    PUSH_TYPE = "j"


@AbstractBytecodeContainer.register_instruction
class DConst0(ConstPush):
    OPCODES = {0x0E}
    PUSHES = 0
    PUSH_TYPE = "d"


@AbstractBytecodeContainer.register_instruction
class IConst1(ConstPush):
    OPCODES = {0x04}
    PUSHES = 1
    PUSH_TYPE = "i"


@AbstractBytecodeContainer.register_instruction
class DConst1(ConstPush):
    OPCODES = {0x0F}
    PUSHES = 1
    PUSH_TYPE = "d"


@AbstractBytecodeContainer.register_instruction
class IConst2(ConstPush):
    OPCODES = {0x05}
    PUSHES = 2
    PUSH_TYPE = "i"


@AbstractBytecodeContainer.register_instruction
class IConst3(ConstPush):
    OPCODES = {0x06}
    PUSHES = 3
    PUSH_TYPE = "i"


@AbstractBytecodeContainer.register_instruction
class IConst4(ConstPush):
    OPCODES = {0x07}
    PUSHES = 4
    PUSH_TYPE = "i"


@AbstractBytecodeContainer.register_instruction
class IConst5(ConstPush):
    OPCODES = {0x08}
    PUSHES = 5
    PUSH_TYPE = "i"


@AbstractBytecodeContainer.register_instruction
class LConst1(ConstPush):
    OPCODES = {0x0A}
    PUSHES = 1
    PUSH_TYPE = "j"


@AbstractBytecodeContainer.register_instruction
class FConst0(ConstPush):
    OPCODES = {0x0B}
    PUSHES = 0.0
    PUSH_TYPE = "f"


@AbstractBytecodeContainer.register_instruction
class FConst1(ConstPush):
    OPCODES = {0x0C}
    PUSHES = 1.0
    PUSH_TYPE = "f"


@AbstractBytecodeContainer.register_instruction
class FConst2(ConstPush):
    OPCODES = {0x0D}
    PUSHES = 2.0
    PUSH_TYPE = "f"


@AbstractBytecodeContainer.register_instruction
class BiPush(OpcodeInstruction):
    OPCODES = {0x10}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U1_S.unpack(data[index: index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push(data)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.push("B")

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_CONST, builder.add_const(bytes([prepared_data])))


@AbstractBytecodeContainer.register_instruction
class SiPush(OpcodeInstruction):
    OPCODES = {0x11}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U2_S.unpack(data[index: index + 2])[0], 3

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push(data)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.push("S")

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_CONST, builder.add_const(prepared_data))


@AbstractBytecodeContainer.register_instruction
class LDC(OpcodeInstruction):
    OPCODES = {0x12}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return data[index], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push(
            jvm.util.decode_cp_constant(
                stack.method.class_file.cp[data - 1],
                version=stack.method.class_file.internal_version,
                vm=stack.method.get_parent_class().vm,
            )
        )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.push(None)  # todo: add type

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_CONST, builder.add_const(jvm.util.decode_cp_constant(
            container.method.class_file.cp[prepared_data - 1],
            version=container.method.class_file.internal_version,
            vm=container.method.get_parent_class().vm,
        )))


@AbstractBytecodeContainer.register_instruction
class LDC_W(LDC):
    OPCODES = {0x13, 0x14}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U2.unpack(data[index: index + 2])[0], 3


@AbstractBytecodeContainer.register_instruction
class ArrayLoad(OpcodeInstruction):
    OPCODES = {0x32, 0x2E, 0x33, 0x31}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        index = stack.pop()
        array = stack.pop()

        if index is None:
            raise StackCollectingException("NullPointerException: index is null")

        if array is None:
            raise StackCollectingException("NullPointerException: array is null")

        stack.push(array[index])

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop_expect_type("i", "j")
        stack.pop()
        stack.push(None)  # todo: add type here

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.BINARY_SUBSCR)


@AbstractBytecodeContainer.register_instruction
class ArrayStore(OpcodeInstruction):
    OPCODES = {0x53, 0x4F, 0x50, 0x54, 0x52, 0x51, 0x55}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        value = stack.pop()
        index = stack.pop()
        array = stack.pop()

        if index is None:
            raise StackCollectingException("NullPointerException: index is null")

        if array is None:
            raise StackCollectingException("NullPointerException: array is null")

        if index < 0:
            raise StackCollectingException(f"Array index out of range: {index} < 0")

        if index >= len(array):
            raise StackCollectingException(f"Array index out of range: {index} >= {len(array)}")

        array[index] = value

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.pop()
        stack.pop_expect_type("i", "j")
        stack.pop()

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.ROT_THREE)
        builder.add_instruction(PyOpcodes.STORE_SUBSCR)


@AbstractBytecodeContainer.register_instruction
class Load(OpcodeInstruction):
    OPCODES = {0x19, 0x15, 0x18, 0x17, 0x16}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U1.unpack(data[index: index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push(stack.local_vars[data])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        if prepared_data >= container.code.max_locals:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: {prepared_data} does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.push(None)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_FAST, prepared_data)


@AbstractBytecodeContainer.register_instruction
class Load0(OpcodeInstruction):
    OPCODES = {0x2A, 0x1A, 0x22, 0x26, 0x1E}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push(stack.local_vars[0])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        if container.code.max_locals <= 0:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 0 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.push(None)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_FAST, 0)


@AbstractBytecodeContainer.register_instruction
class Load1(OpcodeInstruction):
    OPCODES = {0x2B, 0x1B, 0x23, 0x27, 0x1F}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push(stack.local_vars[1])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        if container.code.max_locals <= 1:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 1 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.push(None)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_FAST, 1)


@AbstractBytecodeContainer.register_instruction
class Load2(OpcodeInstruction):
    OPCODES = {0x2C, 0x1C, 0x24, 0x28, 0x20}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push(stack.local_vars[2])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        if container.code.max_locals <= 2:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 2 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.push(None)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_FAST, 2)


@AbstractBytecodeContainer.register_instruction
class Load3(OpcodeInstruction):
    OPCODES = {0x2D, 0x1D, 0x25, 0x29, 0x21}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push(stack.local_vars[3])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        if container.code.max_locals <= 3:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 3 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.push(None)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_FAST, 3)


@AbstractBytecodeContainer.register_instruction
class Store(OpcodeInstruction):
    OPCODES = {0x3A, 0x36, 0x39, 0x38, 0x37}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U1.unpack(data[index: index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.local_vars[data] = stack.pop()

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        if prepared_data >= container.code.max_locals:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: {prepared_data} does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.pop()

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.STORE_FAST, prepared_data)


@AbstractBytecodeContainer.register_instruction
class Store0(OpcodeInstruction):
    OPCODES = {0x4B, 0x3B, 0x47, 0x43, 0x3F}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.local_vars[0] = stack.pop()

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        if container.code.max_locals <= 0:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 0 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.pop()

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.STORE_FAST, 0)


@AbstractBytecodeContainer.register_instruction
class Store1(OpcodeInstruction):
    OPCODES = {0x4C, 0x3C, 0x48, 0x44, 0x40}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.local_vars[1] = stack.pop()

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        if container.code.max_locals <= 1:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 1 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.pop()

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.STORE_FAST, 1)


@AbstractBytecodeContainer.register_instruction
class Store2(OpcodeInstruction):
    OPCODES = {0x4D, 0x3D, 0x49, 0x45, 0x41}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.local_vars[2] = stack.pop()

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        if container.code.max_locals <= 2:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 2 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.pop()

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.STORE_FAST, 2)


@AbstractBytecodeContainer.register_instruction
class Store3(OpcodeInstruction):
    OPCODES = {0x4E, 0x3E, 0x4A, 0x46, 0x42}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.local_vars[3] = stack.pop()

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        if container.code.max_locals <= 3:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 3 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.pop()

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.STORE_FAST, 3)


@AbstractBytecodeContainer.register_instruction
class POP(OpcodeInstruction):
    OPCODES = {0x57}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.pop()

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.pop()

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.POP_TOP)


@AbstractBytecodeContainer.register_instruction
class POP2(OpcodeInstruction):
    OPCODES = {0x58}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        # todo: check computation type
        stack.pop()
        stack.pop()

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer,
                       stack: AbstractStack):
        stack.pop()
        stack.pop()

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.POP_TOP)
        builder.add_instruction(PyOpcodes.POP_TOP)


@AbstractBytecodeContainer.register_instruction
class DUP(OpcodeInstruction):
    OPCODES = {0x59}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        v = stack.pop()
        stack.push(v)
        stack.push(v)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        t = stack.pop()
        stack.push(t)
        stack.push(t)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.DUP_TOP)


@AbstractBytecodeContainer.register_instruction
class DUP2(OpcodeInstruction):
    OPCODES = {0x5C}
    # todo: check for double & long!

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        v1 = stack.pop()
        v2 = stack.pop()
        stack.push(v2)
        stack.push(v1)
        stack.push(v2)
        stack.push(v1)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        v1 = stack.pop()
        v2 = stack.pop()
        stack.push(v2)
        stack.push(v1)
        stack.push(v2)
        stack.push(v1)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.DUP_TOP)  # todo: do real opcode here!


@AbstractBytecodeContainer.register_instruction
class DUP_X1(OpcodeInstruction):
    OPCODES = {0x5A}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        a, b = stack.pop(), stack.pop()
        stack.push(a)
        stack.push(b)
        stack.push(a)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        a, b = stack.pop(), stack.pop()
        stack.push(a)
        stack.push(b)
        stack.push(a)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.DUP_TOP)
        builder.add_instruction(PyOpcodes.ROT_THREE)


@AbstractBytecodeContainer.register_instruction
class ADD(OpcodeInstruction):
    OPCODES = {0x60, 0x63, 0x62}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        b, a = stack.pop(), stack.pop()
        try:
            stack.push(a + b)
        except TypeError:
            raise

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.BINARY_ADD)


@AbstractBytecodeContainer.register_instruction
class SUB(OpcodeInstruction):
    OPCODES = {0x66, 0x64, 0x67, 0x65}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        b, a = stack.pop(), stack.pop()
        stack.push(b - a)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.BINARY_SUBTRACT)


@AbstractBytecodeContainer.register_instruction
class IDIV(OpcodeInstruction):
    OPCODES = {0x6C}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        b, a = stack.pop(), stack.pop()
        stack.push(a // b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.BINARY_FLOOR_DIVIDE)


@AbstractBytecodeContainer.register_instruction
class FDIV(OpcodeInstruction):
    OPCODES = {0x6E, 0x6F}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        b, a = stack.pop(), stack.pop()
        stack.push(a / b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.BINARY_TRUE_DIVIDE)


@AbstractBytecodeContainer.register_instruction
class Rem(OpcodeInstruction):
    OPCODES = {0x70, 0x71}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        b, a = stack.pop(), stack.pop()
        stack.push(int(a - (a / b) * b))

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)


@AbstractBytecodeContainer.register_instruction
class SHL(OpcodeInstruction):
    OPCODES = {0x78}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        b, a = stack.pop(), stack.pop()
        stack.push(a << b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.BINARY_LSHIFT)


@AbstractBytecodeContainer.register_instruction
class SHR(OpcodeInstruction):
    OPCODES = {0x7A}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        b, a = stack.pop(), stack.pop()
        stack.push(a >> b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.BINARY_RSHIFT)


@AbstractBytecodeContainer.register_instruction
class AND(OpcodeInstruction):
    OPCODES = {0x7E}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        b, a = stack.pop(), stack.pop()
        stack.push(a & b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.BINARY_AND)


@AbstractBytecodeContainer.register_instruction
class OR(OpcodeInstruction):
    OPCODES = {0x80}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        b, a = stack.pop(), stack.pop()
        stack.push(a | b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.BINARY_OR)


@AbstractBytecodeContainer.register_instruction
class IINC(OpcodeInstruction):
    OPCODES = {0x84}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Tuple[int, int], int]:
        return (
           data[index],
           jvm.util.U1_S.unpack(data[index + 1: index + 2])[0],
        ), 3

    @classmethod
    def invoke(cls, data: typing.Tuple[int, int], stack: AbstractStack):
        stack.local_vars[data[0]] += data[1]

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Tuple[int, int], container: AbstractBytecodeContainer):
        if prepared_data[0] >= container.code.max_locals:
            raise StackCollectingException(f"local var index {prepared_data[0]} out of range")

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Tuple[int, int],
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.LOAD_FAST, prepared_data[0])
        builder.add_instruction(PyOpcodes.LOAD_CONST, builder.add_const(prepared_data[1]))
        builder.add_instruction(PyOpcodes.INPLACE_ADD)
        builder.add_instruction(PyOpcodes.STORE_FAST, prepared_data[0])


@AbstractBytecodeContainer.register_instruction
class CompareTwo(OpcodeInstruction):
    OPCODES = {0x94, 0x95, 0x96, 0x97, 0x98}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        b, a = stack.pop(), stack.pop()

        if a == b:
            stack.push(0)
        elif a > b:
            stack.push(1)
        else:
            stack.push(-1)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push("i")

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any,
                                             container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        builder.add_instruction(PyOpcodes.DUP_TOP_TWO)
        builder.add_instruction(PyOpcodes.COMPARE_OP, builder.add_comparator("=="))
        builder.add_instruction(PyOpcodes.POP_JUMP_IF_FALSE, builder.real_from_offset(6))

        builder.add_instruction(PyOpcodes.LOAD_CONST, builder.add_const(0))
        builder.add_instruction(PyOpcodes.JUMP_ABSOLUTE, builder.real_from_offset(16))

        builder.add_instruction(PyOpcodes.DUP_TOP_TWO)
        builder.add_instruction(PyOpcodes.COMPARE_OP, builder.add_comparator(">"))
        builder.add_instruction(PyOpcodes.POP_JUMP_IF_FALSE, builder.real_from_offset(6))

        builder.add_instruction(PyOpcodes.LOAD_CONST, builder.add_const(1))
        builder.add_instruction(PyOpcodes.JUMP_ABSOLUTE, builder.real_from_offset(4))

        builder.add_instruction(PyOpcodes.LOAD_CONST, builder.add_const(-1))


class CompareHelper(OpcodeInstruction, ABC):
    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U2_S.unpack(data[index: index + 2])[0], 3

    @classmethod
    def code_reference_changer(
        cls,
        container: AbstractBytecodeContainer,
        prepared_data: int,
        instruction_index: int,
        old_index: int,
        checker: typing.Callable[[int], int],
    ):
        return checker(prepared_data + old_index) - instruction_index

    @classmethod
    def validate(cls, command_index: int, prepared_data: int, container: AbstractBytecodeContainer):
        if command_index + prepared_data < 0:
            raise StackCollectingException(f"opcode index {command_index + prepared_data} is < 0 (OutOfBoundError)")

        elif command_index + prepared_data >= len(container.decoded_code):
            raise StackCollectingException(f"opcode index {command_index + prepared_data} is >= {len(container.decoded_code)} (OutOfBoundError)")

        elif container.decoded_code[command_index + prepared_data] is None:
            raise StackCollectingException(f"opcode index {command_index+prepared_data} is pointing into opcode BODY, not HEAD (bound 0 <= {command_index+prepared_data} < {len(container.decoded_code)})")


class SingleCompare(CompareHelper, ABC):
    @classmethod
    def validate_stack(cls, command_index, prepared_data: int, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.branch(prepared_data)


class DoubleCompare(CompareHelper, ABC):
    @classmethod
    def validate_stack(cls, command_index, prepared_data: int, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.pop()
        stack.branch(prepared_data)


@AbstractBytecodeContainer.register_instruction
class IfLT(DoubleCompare):
    OPCODES = {0x97}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() > stack.pop():
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfGT(DoubleCompare):
    OPCODES = {0xA3}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() < stack.pop():
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfEq0(SingleCompare):
    OPCODES = {0x99}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() == 0:
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfNEq0(SingleCompare):
    OPCODES = {0x9A}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() != 0:
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfLT0(SingleCompare):
    OPCODES = {0x9B}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() < 0:
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfGE0(SingleCompare):
    OPCODES = {0x9C}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() >= 0:
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfGT0(SingleCompare):
    OPCODES = {0x9D}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() > 0:
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfLE0(SingleCompare):
    OPCODES = {0x9E}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() <= 0:
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfEq(DoubleCompare):
    OPCODES = {0x9F, 0xA5}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() == stack.pop():
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfNE(DoubleCompare):
    OPCODES = {0xA0, 0xA6}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() != stack.pop():
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfLt(DoubleCompare):
    OPCODES = {0xA1}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() > stack.pop():
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfGe(DoubleCompare):
    OPCODES = {0xA2}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() <= stack.pop():
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfLe(DoubleCompare):
    OPCODES = {0xA4}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack) -> bool:
        if stack.pop() >= stack.pop():
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class Goto(CompareHelper):
    OPCODES = {0xA7}

    @classmethod
    def invoke(cls, data: int, stack: AbstractStack):
        stack.cp += data
        return True

    @classmethod
    def validate_stack(cls, command_index, prepared_data: int, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.cp += prepared_data


@AbstractBytecodeContainer.register_instruction
class AReturn(OpcodeInstruction):
    OPCODES = {0xB0, 0xAC, 0xAE}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.end(stack.pop())

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.cp = -1


@AbstractBytecodeContainer.register_instruction
class Return(OpcodeInstruction):
    OPCODES = {0xB1}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.end()

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.cp = -1


@AbstractBytecodeContainer.register_instruction
class GetStatic(CPLinkedInstruction):
    OPCODES = {0xB2}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        d, i = super().decode(data, index, class_file)
        return (d[1][1][1], d[2][1][1], d[2][2][1]), i

    @classmethod
    def invoke(cls, data: typing.Tuple[str, str, str], stack: AbstractStack):
        cls_name, name, T = data
        java_class = stack.vm.get_class(
            cls_name, version=stack.method.class_file.internal_version
        )
        stack.push(java_class.get_static_attribute(name, expected_type=T))

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Tuple[str, str, str], container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.push(prepared_data[2])


@AbstractBytecodeContainer.register_instruction
class PutStatic(CPLinkedInstruction):
    OPCODES = {0xB3}

    @classmethod
    def decode(
            cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        d, i = super().decode(data, index, class_file)
        return (d[1][1][1], d[2][1][1]), i

    @classmethod
    def invoke(cls, data: typing.Tuple[str, str], stack: AbstractStack):
        cls_name, name = data
        java_class = stack.vm.get_class(
            cls_name, version=stack.method.class_file.internal_version
        )

        value = stack.pop()
        java_class.set_static_attribute(name, value)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()


@AbstractBytecodeContainer.register_instruction
class GetField(CPLinkedInstruction):
    OPCODES = {0xB4}

    @classmethod
    def decode(
            cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        d, i = super().decode(data, index, class_file)
        return d[2][1][1], i

    @classmethod
    def invoke(cls, name: str, stack: AbstractStack):
        obj = stack.pop()

        if obj is None:
            raise StackCollectingException(f"NullPointerException: object is None; Cannot get attribute '{name}'")

        try:
            stack.push(obj.get_field(name))
        except (KeyError, AttributeError):
            if hasattr(obj, "get_class") and isinstance(obj.get_class(), jvm.Java.JavaBytecodeClass):
                raise StackCollectingException(
                    f"AttributeError: object {obj} (type {type(obj)}) has no attribute {name}"
                ) from None

            try:
                stack.push(getattr(obj, name))
            except (KeyError, AttributeError):
                raise StackCollectingException(
                    f"AttributeError: object {obj} (type {type(obj)}) has no attribute {name}"
                ) from None

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.push(None)


@AbstractBytecodeContainer.register_instruction
class PutField(CPLinkedInstruction):
    OPCODES = {0xB5}

    @classmethod
    def decode(
            cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Tuple[str, str], int]:
        d, i = super().decode(data, index, class_file)
        return (d[2][1][1], d[1][1][1]), i

    @classmethod
    def invoke(cls, d, stack: AbstractStack):
        name, target_type = d
        value = stack.pop()
        obj = stack.pop()

        if obj is None:
            raise StackCollectingException(f"NullPointerException: obj is null; Cannot set field '{name}' to {value}").add_trace(target_type)

        if not hasattr(obj, "set_field"):
            setattr(obj, name, value)
        else:
            obj.set_field(name, value)

    @classmethod
    def validate_stack(cls, command_index, name: str, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.pop()


@AbstractBytecodeContainer.register_instruction
class InvokeVirtual(CPLinkedInstruction):
    OPCODES = {0xB6}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        # todo: lookup signature and insert here
        args = len(tuple(AbstractRuntime.get_arg_parts_of(prepared_data[2][2][1])))
        [stack.pop() for _ in range(args + 1)]
        stack.push(None)

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        # print(data)
        method = stack.vm.get_method_of_nat(
            data, version=stack.method.class_file.internal_version
        )
        args = stack.runtime.parse_args_from_stack(method, stack, False)

        obj = args[0]

        if obj is not None:
            if not hasattr(obj, "get_class"):
                if hasattr(method, "access") and method.access & 0x0400:
                    raise StackCollectingException(
                        "invalid abstract not-implemented non-reference-able object"
                        + str(obj)
                    )

            else:
                try:
                    cls = obj.get_class()
                except TypeError:
                    pass
                else:
                    method_before = method

                    method = cls.get_method(
                        method.name if hasattr(method, "name") else method.native_name,
                        method.signature
                        if hasattr(method, "signature")
                        else method.native_signature,
                    )

                    # dynamic methods need to be skipped here...
                    # Abstract methods as outer cannot be used, as dynamic is still better than abstract
                    # todo: add some better indicator here
                    if hasattr(method, "__name__") and method.__name__ == "dynamic" and (not method_before.access & 0x0400 if hasattr(method_before, "access") else True):
                        method = method_before

        stack.push(stack.runtime.run_method(method, *args, stack=stack))


@AbstractBytecodeContainer.register_instruction
class InvokeSpecial(CPLinkedInstruction):
    OPCODES = {0xB7}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        arg_types = tuple(AbstractRuntime.get_arg_parts_of(prepared_data[2][2][1]))
        args = len(arg_types)
        [stack.pop()] + [stack.pop_expect_type(arg_types[i]) for i in range(args)]

        if prepared_data[2][1][1] not in (
            "<init>",
            "<clinit>",
        ):
            stack.push(None)

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        method = stack.vm.get_method_of_nat(
            data, version=stack.method.class_file.internal_version
        )
        result = stack.runtime.run_method(
            method, *stack.runtime.parse_args_from_stack(method, stack, False), stack=stack,
        )
        method_name = (method.name if hasattr(method, "name") else method.native_name)
        if method_name not in (
            "<init>",
            "<clinit>",
        ):
            stack.push(result)


@AbstractBytecodeContainer.register_instruction
class InvokeStatic(CPLinkedInstruction):
    OPCODES = {0xB8}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        from jvm.Runtime import Runtime

        args = tuple(Runtime.get_arg_parts_of(prepared_data[2][2][1]))
        [stack.pop_expect_type(arg) for arg in args]
        stack.push(prepared_data[2][2][1].split(")")[-1])

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        method = stack.vm.get_method_of_nat(
            data, version=stack.method.class_file.internal_version
        )
        stack.push(
            stack.runtime.run_method(
                method, *stack.runtime.parse_args_from_stack(method, stack, static=True), stack=stack,
            )
        )


@AbstractBytecodeContainer.register_instruction
class InvokeInterface(CPLinkedInstruction):
    OPCODES = {0xB9}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.cp = -1  # todo: implement

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return (
            class_file.cp[
                jvm.util.U2.unpack(data[index: index + 2])[0] - 1
                ],
            data[index + 2],
        ), 5

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        method = stack.vm.get_method_of_nat(
            data[0], version=stack.method.class_file.internal_version
        )
        args = stack.runtime.parse_args_from_stack(method, stack, False)
        obj = args[0]

        try:
            method = obj.get_class().get_method(
                method.name if hasattr(method, "name") else method.native_name,
                method.signature
                if hasattr(method, "signature")
                else method.native_signature,
            )

        except StackCollectingException as e:
            e.add_trace(f"during resolving interface method for parent {method}")
            raise

        except AttributeError:
            pass

        if hasattr(method, "access") and method.access & 0x0400:
            cls_file = method.class_file

            # todo: move this check into method parsing
            if "AbstractRuntimeVisibleAnnotations" in cls_file.attributes.attributes and any(
                any(e[0] == "java/lang/FunctionalInterface" for e in attr.annotations)
                for attr in cls_file.attributes.attributes["AbstractRuntimeVisibleAnnotations"]
            ):
                args = list(args)
                method = args.pop(0)

        try:
            stack.push(stack.runtime.run_method(method, *args, stack=stack))
        except StackCollectingException as e:
            e.add_trace(f"during invoking interface {method} with {args}")

            if hasattr(method, "class_file"):
                e.add_trace(f"in class {method.class_file}")

            raise


@AbstractBytecodeContainer.register_instruction
class InvokeDynamic(CPLinkedInstruction):
    """
    InvokeDynamic

    Resolves a method (mostly lambda's) onto the stack

    Pops in case they are needed args from the stack

    todo: cache method lookup
    """

    OPCODES = {0xBA}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.cp = -1  # todo: implement

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        cp = class_file.cp[
            jvm.util.U2.unpack(data[index: index + 2])[0] - 1
            ]
        boostrap = class_file.attributes["BootstrapMethods"][0].entries[cp[1]]

        # The type side for the execution
        side = boostrap[0][2][1][1][1]
        return (
            (cp, side, boostrap),
            5,
        )

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        if len(data) != 2:
            raise StackCollectingException(
                f"invalid InvokeDynamic target: target {data[1]} not found!"
            )
        else:
            method, data = data
            # m = stack.vm.get_method_of_nat(data[0])
            call_site = method((data[1][2], data[0], data[1]), data[1][0][2][1][1], data[1][2], stack=stack)
            stack.push(call_site)

    @classmethod
    def optimiser_iteration(
        cls,
        container: AbstractBytecodeContainer,
        prepared_data: typing.Tuple[typing.Any, str],
        instruction_index: int,
    ):
        # todo: add a map here
        if prepared_data[1] == "java/lang/invoke/LambdaMetafactory":
            container.decoded_code[instruction_index] = (
                LambdaInvokeDynamic,
                prepared_data[0],
                5,
            )
        else:
            vm = container.code.class_file.vm
            method = vm.get_method_of_nat(prepared_data[2][0][2])
            return method, (container.code.class_file, prepared_data)


@AbstractBytecodeContainer.register_instruction
class LambdaInvokeDynamic(BaseInstruction):
    """
    Class representing the factory system for a lambda
    """

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.cp = -1  # todo: implement

    class LambdaInvokeDynamicWrapper(jvm.api.AbstractMethod):
        def __init__(
            self, method, name: str, signature: str, extra_args: typing.Iterable
        ):
            super().__init__()
            self.method = method
            self.name = name
            self.signature = signature
            self.extra_args = extra_args
            self.access = method.access  # access stays the same

        def invoke(self, args, stack=None):
            return self(*args)

        def __call__(self, *args):
            return self.method(*self.extra_args, *args)

        def __repr__(self):
            return f"InvokeDynamic::CallSite(wrapping={self.method},add_args={self.extra_args})"

        def get_class(self):
            return self.method.class_file.vm.get_class("java/lang/reflect/Method")

    class LambdaNewInvokeDynamicWrapper(LambdaInvokeDynamicWrapper):
        def __call__(self, *args):
            instance = self.method.class_file.create_instance()
            self.method(instance, *self.extra_args, *args)
            return instance

        def __repr__(self):
            return f"InvokeDynamic::CallSite::new(wrapping={self.method},add_args={self.extra_args})"

    class LambdaAbstractInvokeDynamicWrapper(LambdaInvokeDynamicWrapper):
        def __call__(self, *args):
            method = (
                args[0].get_class().get_method(self.method.name, self.method.signature)
            )
            return method(*self.extra_args, *args)

        def __repr__(self):
            return f"InvokeDynamic::CallSite::around_abstract(wrapping={self.method},add_args={self.extra_args})"

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        if callable(data):
            stack.push(data)
            return

        boostrap = stack.method.class_file.attributes["BootstrapMethods"][0].entries[
            data[1]
        ]
        nat = data[2]

        target_nat = boostrap[1][1][2][2]

        # print("invokedynamic debug", nat, "\n", boostrap)

        try:
            cls_file = stack.vm.get_class(
                boostrap[1][1][2][1][1][1],
                version=stack.method.class_file.internal_version,
            )
            method = cls_file.get_method(target_nat[1][1], target_nat[2][1])
            outer_signature = boostrap[1][0][1][1]

            extra_args = []

            inner_args = len(
                list(
                    stack.runtime.get_arg_parts_of(
                        method.signature
                        if hasattr(method, "signature")
                        else method.native_signature
                    )
                )
            )
            outer_args = len(list(stack.runtime.get_arg_parts_of(outer_signature)))

            # have we args to give from the current runtime?
            if inner_args > outer_args:
                try:
                    extra_args += [stack.pop() for _ in range(inner_args - outer_args)]
                except StackCollectingException as e:
                    e.add_trace(f"during invoke-dynamic arg pop towards method {method}")
                    raise

            if not hasattr(method, "name") and not hasattr(method, "native_name"):
                raise StackCollectingException(
                    f"InvokeDynamic target method is no real method: {method}, and as such cannot be InvokeDynamic-linked"
                )

            method_name = method.name if hasattr(method, "name") else method.native_name

            # init methods are special, we need to wrap it into a special object for object creation
            if method_name == "<init>":
                # print("InvokeDynamic short-path <init>", method, outer_signature, extra_args)
                method = cls.LambdaNewInvokeDynamicWrapper(
                    method, method_name, outer_signature, tuple(reversed(extra_args))
                )
                stack.push(method)
                return

            # print("long InvokeDynamic", method, outer_signature)

            if not hasattr(method, "name") and not hasattr(method, "native_name"):
                raise StackCollectingException(
                    f"InvokeDynamic target method is no real method: {method}, and as such cannot be InvokeDynamic-linked"
                )

            if outer_args > inner_args:
                if method.access & 0x0400:
                    method = cls.LambdaInvokeDynamicWrapper(
                        cls.LambdaAbstractInvokeDynamicWrapper(
                            method,
                            method.name
                            if hasattr(method, "name")
                            else method.native_name,
                            outer_signature,
                            [],
                        ),
                        method.name,
                        outer_signature,
                        tuple(reversed(extra_args)),
                    )
                else:
                    method = cls.LambdaInvokeDynamicWrapper(
                        method,
                        method.name if hasattr(method, "name") else method.native_name,
                        outer_signature,
                        tuple(reversed(extra_args)),
                    )

                method.access ^= 0x0008  # if we are dynamic but we expose object, we are no longer dynamic!

                stack.push(method)
                return

            if not hasattr(method, "access"):
                raise StackCollectingException(method)

            # for non-static methods, we need to pop the object from the stack as it might reference it
            # for non-static methods exposing the object attribute as first parameter
            if not method.access & 0x0008:
                # print("dynamic InvokeDynamic")
                extra_args.append(stack.pop())

                if method.access & 0x0400:  # is the method abstract
                    # print("lambdaAroundAbstract", len(extra_args), extra_args)
                    # print("abstract", method)
                    method = cls.LambdaAbstractInvokeDynamicWrapper(
                        method,
                        method_name,
                        outer_signature,
                        tuple(reversed(extra_args)),
                    )

                    stack.push(method)
                    return

            # If we have any prepared arguments, we need to wrap it in another structure for
            #    adding the args before invocation & updating the outer signature of the method to match
            if len(extra_args) > 0 or outer_args > inner_args:
                # print("additional", len(extra_args), extra_args)
                # print("exposed signature", outer_signature)
                method = cls.LambdaInvokeDynamicWrapper(
                    method, method_name, outer_signature, tuple(reversed(extra_args))
                )

                stack.push(method)
                return

        except StackCollectingException as e:
            e.add_trace("during resolving InvokeDynamic")
            e.add_trace(str(boostrap[0]))
            e.add_trace(str(boostrap[1]))
            e.add_trace(str(nat))
            raise

        except:
            e = StackCollectingException("during resolving InvokeDynamic")
            e.add_trace(str(boostrap[0]))
            e.add_trace(str(boostrap[1]))
            e.add_trace(str(nat))
            raise e

        stack.push(method)


@AbstractBytecodeContainer.register_instruction
class New(CPLinkedInstruction):
    OPCODES = {0xBB}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.push(None)

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        c = stack.vm.get_class(
            data[1][1], version=stack.method.class_file.internal_version
        )
        stack.push(c.create_instance())


@AbstractBytecodeContainer.register_instruction
class NewArray(CPLinkedInstruction):
    OPCODES = {0xBC}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop_expect_type("i", "j")
        stack.push(None)

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U1.unpack(data[index: index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push([None] * stack.pop())


@AbstractBytecodeContainer.register_instruction
class ANewArray(CPLinkedInstruction):
    OPCODES = {0xBD}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop_expect_type("i", "j")
        stack.push(None)

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push([None] * stack.pop())


@AbstractBytecodeContainer.register_instruction
class ArrayLength(OpcodeInstruction):
    """
    Resolves the length of an array

    In some contexts, this result is constant in each call
    Can we detect this?
    """

    OPCODES = {0xBE}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        a = stack.pop()

        if a is None:
            raise StackCollectingException("array is None")

        stack.push(len(a))

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.push("i")


@AbstractBytecodeContainer.register_instruction
class AThrow(OpcodeInstruction):
    """
    Throws an exception

    In some cases, this raise can be moved up some instructions when no side effect is detected
    """

    OPCODES = {0xBF}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        exception = stack.pop()
        stack.stack.clear()
        stack.push(exception)
        raise StackCollectingException("User raised exception: "+str(exception), base=exception).add_trace(exception)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.cp = -1


@AbstractBytecodeContainer.register_instruction
class CheckCast(CPLinkedInstruction):
    OPCODES = {0xC0}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        pass  # todo: implement


@AbstractBytecodeContainer.register_instruction
class InstanceOf(CPLinkedInstruction):
    OPCODES = {0xC1}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        obj = stack.pop()

        if not hasattr(obj, "get_class"):
            # todo: we need a fix here!
            stack.push(0)
        else:
            stack.push(int(obj is None or obj.get_class().is_subclass_of(data[1][1])))

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()
        stack.push("Z")


@AbstractBytecodeContainer.register_instruction
class MultiANewArray(OpcodeInstruction):
    OPCODES = {0xC5}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return (data[index:index+2], data[index+2]), 4

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        dimensions = [stack.pop() for _ in range(data[1])]
        data = [None] * dimensions.pop(0)

        for e in dimensions:
            data = [copy.deepcopy(data) for _ in range(e)]

        stack.push(data)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        for _ in range(prepared_data[1]):
            stack.pop_expect_type("i", "j")
        stack.push(None)


@AbstractBytecodeContainer.register_instruction
class IfNull(SingleCompare):
    OPCODES = {0xC6}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack) -> bool:
        if stack.pop() is None:
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class IfNonNull(SingleCompare):
    OPCODES = {0xC7}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack) -> bool:
        if stack.pop() is not None:
            stack.cp += data
            return True


@AbstractBytecodeContainer.register_instruction
class Mul(OpcodeInstruction):
    OPCODES = {0x68, 0x6B, 0x6A}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push(stack.pop() * stack.pop())

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        t = stack.pop()
        stack.pop_expect_type(t)
        stack.push(t)


@AbstractBytecodeContainer.register_instruction
class NEG(OpcodeInstruction):
    OPCODES = {0x76, 0x77}

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack):
        stack.push(-stack.pop())

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        t = stack.pop()
        stack.push(t)


@AbstractBytecodeContainer.register_instruction
class TableSwitch(OpcodeInstruction):
    """
    TableSwitch instruction
    Similar to LookupSwitch, but in theory faster
    """

    OPCODES = {0xAA}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        index2offset = array.ArrayType("l")
        initial = index

        while index % 4 != 0:
            index += 1

        default = jvm.util.pop_u4_s(data[index:])
        index += 4

        low = jvm.util.pop_u4_s(data[index:])
        index += 4

        high = jvm.util.pop_u4_s(data[index:])
        index += 4

        offsets = [
            jvm.util.pop_u4_s(data[index + i * 4:])
            for i in range(high - low + 1)
        ]

        index2offset.extend(offsets)

        index += (high - low + 1) * 4
        return (default, low, high, index2offset), index - initial + 1

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack) -> bool:
        index = stack.pop()

        if index < data[1] or index > data[2]:
            stack.cp += data[0]
        else:
            stack.cp += data[3][index - data[1]]

        return True

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()

        for offset in prepared_data[3]:
            stack.branch(offset)

        stack.cp += prepared_data[0]

    @classmethod
    def code_reference_changer(
        cls,
        container: AbstractBytecodeContainer,
        prepared_data: typing.Any,
        instruction_index: int,
        old_index: int,
        checker: typing.Callable[[int], int],
    ):
        default, low, high, offsets = prepared_data
        return checker(default + old_index) - instruction_index, low, high, array.ArrayType("l", [checker(e + old_index) - instruction_index for e in offsets])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        for offset in prepared_data[3]:
            CompareHelper.validate(command_index, offset, container)
        CompareHelper.validate(command_index, prepared_data[0], container)


@AbstractBytecodeContainer.register_instruction
class LookupSwitch(OpcodeInstruction):
    """
    LookupSwitch Instruction

    Specified by https://docs.oracle.com/javase/specs/jvms/se16/html/jvms-6.htm

    Structure
    0xAA [type byte]
    0-3 bytes padding to make next byte align to 4 byte blocks
    The next 4 bytes are the default offset, the next 4 the case counts.
    Followed by the respective count of 4 bytes case key and 4 bytes case offset.

    Optimisation possibilities:
    - convert into tableswitch when structure is close to it
    - for enums: use tableswitch with special case attribute on the enum entries
    - use simple if-elif-else structure for small examples
    - when block jumped to is only used to this part, we can extract it into a subroutine implemented in python when
        possible
    - instead of doing simple if's in code, we can use this structure with hash to decide between multile parts

    Implementation details
        We use a while loop and pop bytes until byte alignment is reached
        We use the pop_u4_s instruction for popping the 4 byte data
        We store the pairs into a dict structure
        We raise a StackCollectingException when the dict construction fails, we include the amount of entries and the default offset

    Safety checks
        Load-time:
        - all offsets must be valid

        Optimisation in-place:
        - jumps to head of instruction must be still valid
        - subroutines must be correctly linked & returned back

        Run-time:
        - value must be int(-like)

    Exceptions:
        StackCollectingException(StackUnderflowException): when no key is on the stack
        <some error during wrong offsets>

    todo: somehow, this does not 100% work...
    """

    OPCODES = {0xAB}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        before = index

        # offset binding
        while index % 4 != 0:
            index += 1

        # the static HEAD
        default = jvm.util.pop_u4_s(data[index:])
        index += 4
        npairs = jvm.util.pop_u4_s(data[index:])
        index += 4

        # And now, the key-value pairs
        try:
            pairs = {
                jvm.util.pop_u4_s(
                    data[index + i * 8:]
                ): jvm.util.pop_u4_s(data[index + i * 8 + 4:])
                for i in range(npairs)
            }
            index += npairs * 8
        except:
            raise StackCollectingException(
                f"during decoding lookupswitch of {npairs} entries, defaulting to {default}"
            )

        return (default, pairs), index - before + 1

    @classmethod
    def invoke(cls, data: typing.Any, stack: AbstractStack) -> bool:
        key = stack.pop()

        # todo: do some clever checks here...
        if key not in data[1]:
            stack.cp += data[0]
        else:
            stack.cp += data[1][key]

        return True

    @classmethod
    def code_reference_changer(
        cls,
        container: AbstractBytecodeContainer,
        prepared_data: typing.Any,
        instruction_index: int,
        old_index: int,
        checker: typing.Callable[[int], int],
    ):
        default, pairs = prepared_data
        return checker(default + old_index) - instruction_index, {e[0]: checker(e[1] + old_index) - instruction_index for e in pairs.items()}

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        for offset in prepared_data[1].values():
            CompareHelper.validate(command_index, offset, container)

        CompareHelper.validate(command_index, prepared_data[0], container)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        stack.pop()

        for offset in prepared_data[1].values():
            stack.branch(offset)

        # the default offset goes here...
        stack.cp += prepared_data[0]