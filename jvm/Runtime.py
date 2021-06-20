"""
mcpython - a minecraft clone written in python licenced under the MIT-licence 
(https://github.com/mcpython4-coding/core)

Contributors: uuk, xkcdjerry (inactive)

Based on the game of fogleman (https://github.com/fogleman/Minecraft), licenced under the MIT-licence
Original game "minecraft" by Mojang Studios (www.minecraft.net), licenced under the EULA
(https://account.mojang.com/documents/minecraft_eula)
Mod loader inspired by "Minecraft Forge" (https://github.com/MinecraftForge/MinecraftForge) and similar

This project is not official by mojang and does not relate to it.
"""
import sys
import typing
from abc import ABC

import jvm.Java
from mcpython import logger
from jvm.JavaExceptionStack import StackCollectingException

DEBUG = "--debug-vm" in sys.argv


class Runtime:
    """
    A Runtime is a "frame" in the current VM
    Each thread needs an own Runtime
    A Runtime hold the "flow" between methods
    """

    def __init__(self):
        self.stacks: typing.List["Stack"] = []

    def spawn_stack(self):
        stack = Stack()
        stack.runtime = self
        self.stacks.append(stack)
        return stack

    def run_method(
        self,
        method: typing.Union[jvm.Java.JavaMethod, typing.Callable],
        *args,
    ):
        if callable(method) and not isinstance(
            method, jvm.Java.JavaMethod
        ):
            from mcpython.common.mod.ModLoader import LoadingInterruptException

            try:
                return method(*args)
            except StackCollectingException as e:
                e.add_trace("invoking native " + str(method) + " with " + str(args))
                raise
            except (LoadingInterruptException, SystemExit):
                raise
            except:
                raise StackCollectingException(
                    f"during invoking native {method} with {args}"
                )

        if method.code_repr is None:
            try:
                code = method.attributes["Code"][0]
            except KeyError:
                raise StackCollectingException(
                    f"Abstract method call onto {method} with args {args}; Code attribute not found"
                )

            method.code_repr = BytecodeRepr(code)

        stack = self.spawn_stack()

        stack.code = method.code_repr
        stack.method = method
        method.code_repr.prepare_stack(stack)
        stack.local_vars[: len(args)] = list(args)

        stack.run()

        return stack.return_value

    def get_arg_parts_of(
        self,
        method: typing.Union[jvm.Java.JavaMethod, typing.Callable],
    ) -> typing.Iterator[str]:

        if hasattr(method, "signature"):
            signature = method.signature
        elif hasattr(method, "native_signature"):
            signature = method.native_signature
        elif isinstance(method, str):
            signature = method
        else:
            raise ValueError(method)

        if not signature.startswith("("):
            raise StackCollectingException(f"invalid signature: {signature}")

        v = signature.removeprefix("(").split(")")[0]
        i = 0
        start = 0

        try:
            while i < len(v):
                is_array = False

                if v[i] == "[":
                    is_array = True

                if v[i] == "L":
                    i = v.index(";", i) + 1
                    yield v[start:i], False
                else:
                    i += 1
                    if not is_array:
                        yield v[start:i], v[i - 1] in "DJ"

                if not is_array:
                    start = i
        except:
            raise StackCollectingException(f"cannot parse argument list {signature}")

    def parse_args_from_stack(self, method, stack, static=False):
        try:
            parts = tuple(self.get_arg_parts_of(method))
            previous_count = len(stack.stack)
        except StackCollectingException as e:
            e.add_trace("during parsing args").add_trace(str(stack.stack))
            raise

        try:
            args = [stack.pop() for _ in range(len(parts))]

            if not static:
                obj = stack.pop()
                args.append(obj)

        except StackCollectingException as e:
            e.add_trace(
                f"StackUnderflowException during preparing method execution of '{method}' (static: {static}) with stack size before data popping {previous_count}, expecting len(parts) {parts}"
            )
            raise

        if isinstance(method, jvm.Java.JavaMethod):
            offset = 0
            for i, (_, state) in enumerate(parts):
                if state:
                    args.insert(i + offset, None)
                    offset += 1

        return tuple(reversed(args))


class Stack:
    def __init__(self):
        self.local_vars = []
        self.stack = []
        self.cp = 0

        self.code = None
        self.method = None

        import jvm.Java

        self.vm = jvm.Java.vm

        self.runtime: Runtime = None

        self.return_value = None

        self.code: "BytecodeRepr" = None

    def pop(self):
        if len(self.stack) == 0:
            raise StackCollectingException("StackUnderflowException")

        return self.stack.pop(-1)

    def push(self, value):
        self.stack.append(value)
        return value

    def seek(self):
        return self.stack[-1]

    def end(self, value=None):
        self.cp = -1
        self.return_value = value

    def run(self):
        """
        Runs the data on this stack
        """

        # todo: check for class debugging
        debugging = (
            DEBUG
            or (self.method.class_file.name, self.method.name, self.method.signature)
            in self.method.class_file.vm.debugged_methods
        )

        # todo: is this really needed?
        self.method.class_file.prepare_use()
        if debugging:
            jvm.Java.warn(("launching method", self.method))

        while self.cp != -1:
            instruction = self.code.decoded_code[self.cp]

            if instruction is None:
                raise StackCollectingException(
                    "Instruction jump target was invalid"
                ).add_trace(f"during fetching {self.cp} in {self.method}")

            if debugging:
                jvm.Java.warn(
                    "instruction [info before invoke] " + str((self.cp, instruction))
                )
                jvm.Java.warn(
                    f"stack ({len(self.stack)}): " + str(self.stack)[-300:]
                )
                jvm.Java.warn(
                    f"local ({len(self.local_vars)}: " + str(self.local_vars)[:300]
                )

            try:
                result = instruction[0].invoke(instruction[1], self)
            except StackCollectingException as e:
                e.add_trace(
                    f"during invoking {instruction[0]} in {self.method} [index: {self.cp}]"
                )
                raise
            except:
                raise StackCollectingException(
                    f"Implementation-wise during invoking {instruction[0].__name__} in {self.method} [index: {self.cp}]"
                ).add_trace(str(instruction[1])).add_trace(str(instruction[2]))

            if not result and self.cp != -1:
                try:
                    self.cp += instruction[2]
                except:
                    raise StackCollectingException(
                        f"Implementation-wise during increasing command pointer of {instruction[0].__name__} in {self.method} [index: {self.cp}]"
                    ).add_trace(str(instruction[1])).add_trace(str(instruction[2]))

        if debugging:
            jvm.Java.warn(
                ("finished method", self.method, self.return_value)
            )


class BaseInstruction(ABC):
    """
    Every instruction has to implement this, everything else does not matter
    """

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        raise NotImplementedError

    @classmethod
    def validate(cls, prepared_data: typing.Any, container: "BytecodeRepr"):
        pass

    @classmethod
    def optimiser_iteration(
        cls,
        container: "BytecodeRepr",
        prepared_data: typing.Any,
        instruction_index: int,
    ):
        pass

    @classmethod
    def code_reference_changer(
        cls,
        container: "BytecodeRepr",
        prepared_data: typing.Any,
        instruction_index: int,
        old_index: int,
        checker: typing.Callable[[int], int],
    ):
        pass


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
        pointer = jvm.Java.U2.unpack(data[index : index + 2])[0] - 1
        try:
            return (
                class_file.cp[pointer],
                3,
            )
        except IndexError:
            raise StackCollectingException(
                f"during decoding instruction {cls.__name__} pointing to {pointer}"
            ).add_trace(f"current parsing index: {index}, class: {class_file.name}")


class BytecodeRepr:
    """
    Structure storing instruction references and data from loaded methods
    Created moments before first invocation

    Stores all arrival instructions
    """

    OPCODES: typing.Dict[int, typing.Type[OpcodeInstruction]] = {}

    @classmethod
    def register_instruction(cls, instr):
        if issubclass(instr, OpcodeInstruction):
            for opcode in instr.OPCODES:
                cls.OPCODES[opcode] = instr

        return instr

    def __init__(self, code: jvm.Java.CodeParser):
        self.code = code

        self.decoded_code: typing.List[
            typing.Optional[typing.Tuple[OpcodeInstruction, typing.Any, int]]
        ] = [None] * len(code.code)

        code = bytearray(code.code)
        i = 0
        # print("head", self.code.class_file.name)
        while 0 <= i < len(code):
            # todo: raise error when below 0
            tag = code[i]

            # print("".join(hex(e)[2:] for e in code[i:i+20]))

            if tag in self.OPCODES:
                instr = self.OPCODES[tag]
                # print(instr, code[:5])
                try:
                    data, size = instr.decode(code, i + 1, self.code.class_file)
                except StackCollectingException as e:
                    e.add_trace(
                        f"during decoding instruction {instr} in {self.code.table.parent}"
                    ).add_trace(f"index: {i}, near code: {code[max(0, i-5):i+5]}")
                    raise
                except:
                    raise StackCollectingException(
                        f"during decoding instruction {instr} in {self.code.table.parent}"
                    ).add_trace(f"index: {i}, near code: {code[max(0, i-5):i+5]}")

                # print(data, size, code[i:i+10], len(code))

                self.decoded_code[i] = (instr, data, size)

                i += size

            else:
                raise StackCollectingException(
                    "invalid instruction: "
                    + str(hex(tag))
                    + " (following bits: "
                    + str(code[i : i + 5])
                    + ")"
                ).add_trace(str(self.decoded_code)).add_trace(str(self.code.class_file))

        self.optimiser_iteration()

    def optimiser_iteration(self):
        """
        Runs optimiser code on the internal bytecode
        todo: call this more when the method gets called more often
        """

        for i, e in enumerate(self.decoded_code):
            if e is None:
                continue

            try:
                d = e[0].optimiser_iteration(self, e[1], i)
            except StackCollectingException as e:
                e.add_trace(
                    f"during optimising {e[0].__name__} with data {e[1]} stored at index {i} in {self.code.table.parent}"
                )
                raise

            if d is not None:
                self.decoded_code[i] = (e[0], d) + e[2:]

        # We need to validate it ones now
        self.validate_code()

    def validate_code(self):
        for i, e in enumerate(self.decoded_code):
            if e is None:
                continue

            try:
                e[0].validate(e[1], self)
            except StackCollectingException as e:
                e.add_trace(
                    f"during validating {e[0].__name__} with data {e[1]} stored at index {i} in {self.code.table.parent}"
                )
                raise

    def exchange_jump_offsets(self, begin_section: int, end_section: int, replace_section: typing.List, reference_reworker=lambda address, start, old_end, new_end: 0):
        """
        Helper method for exchanging two section of code with a new one and re-resolving references
        """

        self.decoded_code = self.decoded_code[:begin_section] + replace_section + self.decoded_code[end_section:]
        new_end = begin_section + len(replace_section)

        def resolve(address: int):
            if address < begin_section: return address
            if address > end_section: return address - end_section + new_end
            return reference_reworker(address, begin_section, end_section, new_end)

        for i, instruction in enumerate(self.decoded_code):
            if instruction is None: continue
            new_data = instruction[0].code_reference_changer(self, instruction[1], i, i if i < new_end else i - new_end + end_section, resolve)
            if new_data is None: continue
            self.decoded_code[i] = (instruction[0], new_data) + instruction[2:]

    def prepare_stack(self, stack: Stack):
        """
        Helper method for setting up the stack for execution of this code block
        """
        stack.local_vars = [None] * self.code.max_locals
        stack.cp = 0
        stack.code = self


# Now, the instruction implementations


@BytecodeRepr.register_instruction
class NoOp(OpcodeInstruction):
    # C2 and C3: monitor stuff, as we are not threading, this works as it is
    OPCODES = {0x00, 0x90, 0x88, 0xC2, 0xC3}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        pass


@BytecodeRepr.register_instruction
class Any2Float(OpcodeInstruction):
    OPCODES = {0x87, 0x86}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        v = stack.pop()
        stack.push(float(v) if v is not None else v)


@BytecodeRepr.register_instruction
class Any2Int(OpcodeInstruction):
    OPCODES = {0x8E, 0x8B, 0x8C}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        v = stack.pop()
        stack.push(int(v) if v is not None else v)


class ConstPush(OpcodeInstruction, ABC):
    """
    Base class for instructions pushing pre-defined objects
    """

    PUSHES = None

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(cls.PUSHES)


@BytecodeRepr.register_instruction
class AConstNull(ConstPush):
    OPCODES = {0x01}


@BytecodeRepr.register_instruction
class IConstM1(ConstPush):
    OPCODES = {0x02}
    PUSHES = -1


@BytecodeRepr.register_instruction
class IConst0(ConstPush):
    OPCODES = {0x03, 0x0E, 0x09}
    PUSHES = 0


@BytecodeRepr.register_instruction
class IConst1(ConstPush):
    OPCODES = {0x04, 0x0F}
    PUSHES = 1


@BytecodeRepr.register_instruction
class IConst2(ConstPush):
    OPCODES = {0x05}
    PUSHES = 2


@BytecodeRepr.register_instruction
class IConst3(ConstPush):
    OPCODES = {0x06}
    PUSHES = 3


@BytecodeRepr.register_instruction
class IConst4(ConstPush):
    OPCODES = {0x07}
    PUSHES = 4


@BytecodeRepr.register_instruction
class IConst5(ConstPush):
    OPCODES = {0x08}
    PUSHES = 5


@BytecodeRepr.register_instruction
class FConst0(ConstPush):
    OPCODES = {0x0B}
    PUSHES = 0.0


@BytecodeRepr.register_instruction
class FConst1(ConstPush):
    OPCODES = {0x0C}
    PUSHES = 1.0


@BytecodeRepr.register_instruction
class FConst2(ConstPush):
    OPCODES = {0x0D}
    PUSHES = 2.0


@BytecodeRepr.register_instruction
class BiPush(OpcodeInstruction):
    OPCODES = {0x10}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.Java.U1_S.unpack(data[index : index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(data)


@BytecodeRepr.register_instruction
class SiPush(OpcodeInstruction):
    OPCODES = {0x11}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.Java.U2_S.unpack(data[index : index + 2])[0], 3

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(data)


@BytecodeRepr.register_instruction
class LDC(OpcodeInstruction):
    OPCODES = {0x12}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return data[index], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(
            jvm.Java.decode_cp_constant(
                stack.method.class_file.cp[data - 1],
                version=stack.method.class_file.internal_version,
            )
        )


@BytecodeRepr.register_instruction
class LDC_W(OpcodeInstruction):
    OPCODES = {0x13, 0x14}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.Java.U2.unpack(data[index : index + 2])[0], 3

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(
            jvm.Java.decode_cp_constant(
                stack.method.class_file.cp[data - 1],
                version=stack.method.class_file.internal_version,
            )
        )


@BytecodeRepr.register_instruction
class ArrayLoad(OpcodeInstruction):
    OPCODES = {0x32, 0x2E, 0x33}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        index = stack.pop()
        array = stack.pop()

        if index is None:
            raise StackCollectingException("NullPointerException: index is null")

        if array is None:
            raise StackCollectingException("NullPointerException: array is null")

        stack.push(array[index])


@BytecodeRepr.register_instruction
class ArrayStore(OpcodeInstruction):
    OPCODES = {0x53, 0x4F, 0x50, 0x54, 0x52, 0x51}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        value = stack.pop()
        index = stack.pop()
        array = stack.pop()

        if index is None:
            raise StackCollectingException("NullPointerException: index is null")

        if array is None:
            raise StackCollectingException("NullPointerException: array is null")

        array[index] = value


@BytecodeRepr.register_instruction
class Load(OpcodeInstruction):
    OPCODES = {0x19, 0x15, 0x18, 0x17}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.Java.U1.unpack(data[index : index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(stack.local_vars[data])

    @classmethod
    def validate(cls, prepared_data: typing.Any, container: "BytecodeRepr"):
        if prepared_data >= container.code.max_locals:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: {prepared_data} does not fit into {container.code.max_locals}"
            )


@BytecodeRepr.register_instruction
class Load0(OpcodeInstruction):
    OPCODES = {0x2A, 0x1A, 0x22, 0x26}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(stack.local_vars[0])

    @classmethod
    def validate(cls, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 0:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 0 does not fit into {container.code.max_locals}"
            )


@BytecodeRepr.register_instruction
class Load1(OpcodeInstruction):
    OPCODES = {0x2B, 0x1B, 0x23, 0x27}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(stack.local_vars[1])

    @classmethod
    def validate(cls, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 1:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 1 does not fit into {container.code.max_locals}"
            )


@BytecodeRepr.register_instruction
class Load2(OpcodeInstruction):
    OPCODES = {0x2C, 0x1C, 0x24, 0x28}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(stack.local_vars[2])

    @classmethod
    def validate(cls, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 2:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 2 does not fit into {container.code.max_locals}"
            )


@BytecodeRepr.register_instruction
class Load3(OpcodeInstruction):
    OPCODES = {0x2D, 0x1D, 0x25, 0x29}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(stack.local_vars[3])

    @classmethod
    def validate(cls, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 3:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 3 does not fit into {container.code.max_locals}"
            )


@BytecodeRepr.register_instruction
class Store(OpcodeInstruction):
    OPCODES = {0x3A, 0x36, 0x39, 0x38}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.Java.U1.unpack(data[index : index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[data] = stack.pop()

    @classmethod
    def validate(cls, prepared_data: typing.Any, container: "BytecodeRepr"):
        if prepared_data >= container.code.max_locals:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: {prepared_data} does not fit into {container.code.max_locals}"
            )


@BytecodeRepr.register_instruction
class Store0(OpcodeInstruction):
    OPCODES = {0x4B, 0x3B, 0x47, 0x43}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[0] = stack.pop()

    @classmethod
    def validate(cls, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 0:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 0 does not fit into {container.code.max_locals}"
            )


@BytecodeRepr.register_instruction
class Store1(OpcodeInstruction):
    OPCODES = {0x4C, 0x3C, 0x48, 0x44}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[1] = stack.pop()

    @classmethod
    def validate(cls, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 1:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 1 does not fit into {container.code.max_locals}"
            )


@BytecodeRepr.register_instruction
class Store2(OpcodeInstruction):
    OPCODES = {0x4D, 0x3D, 0x49, 0x45}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[2] = stack.pop()

    @classmethod
    def validate(cls, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 2:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 2 does not fit into {container.code.max_locals}"
            )


@BytecodeRepr.register_instruction
class Store3(OpcodeInstruction):
    OPCODES = {0x4E, 0x3E, 0x4A, 0x46}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[3] = stack.pop()

    @classmethod
    def validate(cls, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 3:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 3 does not fit into {container.code.max_locals}"
            )


@BytecodeRepr.register_instruction
class POP(OpcodeInstruction):
    OPCODES = {0x57}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.pop()


@BytecodeRepr.register_instruction
class DUP(OpcodeInstruction):
    OPCODES = {0x59}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        v = stack.pop()
        stack.push(v)
        stack.push(v)


@BytecodeRepr.register_instruction
class DUP_X1(OpcodeInstruction):
    OPCODES = {0x5A}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        a, b = stack.pop(), stack.pop()
        stack.push(a)
        stack.push(b)
        stack.push(a)


@BytecodeRepr.register_instruction
class ADD(OpcodeInstruction):
    OPCODES = {0x60, 0x63, 0x62}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a + b)


@BytecodeRepr.register_instruction
class SUB(OpcodeInstruction):
    OPCODES = {0x66, 0x64, 0x67}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(b - a)


@BytecodeRepr.register_instruction
class IDIV(OpcodeInstruction):
    OPCODES = {0x6C}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a // b)


@BytecodeRepr.register_instruction
class SHL(OpcodeInstruction):
    OPCODES = {0x78}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a << b)


@BytecodeRepr.register_instruction
class SHR(OpcodeInstruction):
    OPCODES = {0x7A}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a >> b)


@BytecodeRepr.register_instruction
class AND(OpcodeInstruction):
    OPCODES = {0x7E}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a & b)


@BytecodeRepr.register_instruction
class OR(OpcodeInstruction):
    OPCODES = {0x80}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a | b)


@BytecodeRepr.register_instruction
class IINC(OpcodeInstruction):
    OPCODES = {0x84}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return (
            data[index],
            jvm.Java.U1_S.unpack(data[index + 1 : index + 2])[0],
        ), 3

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[data[0]] += data[1]


class CompareHelper(OpcodeInstruction, ABC):
    @classmethod
    def decode(
            cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.Java.U2_S.unpack(data[index: index + 2])[0], 3

    @classmethod
    def code_reference_changer(
            cls,
            container: "BytecodeRepr",
            prepared_data: typing.Any,
            instruction_index: int,
            old_index: int,
            checker: typing.Callable[[int], int],
    ):
        return checker(prepared_data + old_index) - instruction_index


@BytecodeRepr.register_instruction
class IfGE0(CompareHelper):
    OPCODES = {0x9C}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() >= 0:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfEq(CompareHelper):
    OPCODES = {0x9F}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() == stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfNE(CompareHelper):
    OPCODES = {0xA0}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() != stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfLt(CompareHelper):
    OPCODES = {0xA1}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() > stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfGe(CompareHelper):
    OPCODES = {0xA2}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() <= stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfLe(CompareHelper):
    OPCODES = {0xA4}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() >= stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfEq(CompareHelper):
    OPCODES = {0xA5}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() == stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfNEq(CompareHelper):
    OPCODES = {0xA6}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() != stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfEq0(CompareHelper):
    OPCODES = {0x99}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() == 0:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfNEq0(CompareHelper):
    OPCODES = {0x9A}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() != 0:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfLT0(CompareHelper):
    OPCODES = {0x9B}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() < 0:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfLE0(CompareHelper):
    OPCODES = {0x9E}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() <= 0:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class Goto(CompareHelper):
    OPCODES = {0xA7}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.cp += data
        return True


@BytecodeRepr.register_instruction
class AReturn(OpcodeInstruction):
    OPCODES = {0xB0, 0xAC, 0xAE}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.end(stack.pop())


@BytecodeRepr.register_instruction
class Return(OpcodeInstruction):
    OPCODES = {0xB1}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.end()


@BytecodeRepr.register_instruction
class GetStatic(CPLinkedInstruction):
    OPCODES = {0xB2}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        cls_name = data[1][1][1]
        java_class = stack.vm.get_class(
            cls_name, version=stack.method.class_file.internal_version
        )
        name = data[2][1][1]
        stack.push(java_class.get_static_attribute(name, expected_type=data[2][2][1]))


@BytecodeRepr.register_instruction
class PutStatic(CPLinkedInstruction):
    OPCODES = {0xB3}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        cls_name = data[1][1][1]
        java_class = stack.vm.get_class(
            cls_name, version=stack.method.class_file.internal_version
        )
        name = data[2][1][1]
        value = stack.pop()
        java_class.set_static_attribute(name, value)


@BytecodeRepr.register_instruction
class GetField(CPLinkedInstruction):
    OPCODES = {0xB4}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        name = data[2][1][1]
        obj = stack.pop()

        if obj is None:
            raise StackCollectingException("NullPointerException: object is None")

        try:
            stack.push(obj.fields[name])
        except (KeyError, AttributeError):
            raise StackCollectingException(
                f"AttributeError: object {obj} (type {type(obj)}) has no attribute {name}"
            ) from None


@BytecodeRepr.register_instruction
class PutField(CPLinkedInstruction):
    OPCODES = {0xB5}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        name = data[2][1][1]
        value = stack.pop()
        obj = stack.pop()

        if obj is None:
            raise StackCollectingException("NullPointerException: obj is null")

        obj.fields[name] = value


@BytecodeRepr.register_instruction
class InvokeVirtual(CPLinkedInstruction):
    OPCODES = {0xB6}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        # print(data)
        method = stack.vm.get_method_of_nat(
            data, version=stack.method.class_file.internal_version
        )
        args = stack.runtime.parse_args_from_stack(method, stack)

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
                    method = cls.get_method(
                        method.name if hasattr(method, "name") else method.native_name,
                        method.signature
                        if hasattr(method, "signature")
                        else method.native_signature,
                    )

        stack.push(stack.runtime.run_method(method, *args))


@BytecodeRepr.register_instruction
class InvokeSpecial(CPLinkedInstruction):
    OPCODES = {0xB7}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        method = stack.vm.get_method_of_nat(
            data, version=stack.method.class_file.internal_version
        )
        result = stack.runtime.run_method(
            method, *stack.runtime.parse_args_from_stack(method, stack)
        )
        if (method.name if hasattr(method, "name") else method.native_name) not in (
            "<init>",
            "<clinit>",
        ):
            stack.push(result)


@BytecodeRepr.register_instruction
class InvokeStatic(CPLinkedInstruction):
    OPCODES = {0xB8}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        method = stack.vm.get_method_of_nat(
            data, version=stack.method.class_file.internal_version
        )
        stack.push(
            stack.runtime.run_method(
                method, *stack.runtime.parse_args_from_stack(method, stack, static=True)
            )
        )


@BytecodeRepr.register_instruction
class InvokeInterface(CPLinkedInstruction):
    OPCODES = {0xB9}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return (
            class_file.cp[
                jvm.Java.U2.unpack(data[index : index + 2])[0] - 1
            ],
            data[index + 2],
        ), 5

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        method = stack.vm.get_method_of_nat(
            data[0], version=stack.method.class_file.internal_version
        )
        args = stack.runtime.parse_args_from_stack(method, stack)
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
            if "RuntimeVisibleAnnotations" in cls_file.attributes.attributes and any(
                any(e[0] == "java/lang/FunctionalInterface" for e in attr.annotations)
                for attr in cls_file.attributes.attributes["RuntimeVisibleAnnotations"]
            ):
                args = list(args)
                method = args.pop(0)

        try:
            stack.push(stack.runtime.run_method(method, *args))
        except StackCollectingException as e:
            e.add_trace(f"during invoking interface {method} with {args}")

            if hasattr(method, "class_file"):
                e.add_trace(f"in class {method.class_file}")

            raise


@BytecodeRepr.register_instruction
class InvokeDynamic(CPLinkedInstruction):
    """
    InvokeDynamic

    Resolves a method (mostly lambda's) onto the stack

    Pops in case they are needed args from the stack

    todo: cache method lookup
    """

    OPCODES = {0xBA}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        cp = class_file.cp[
            jvm.Java.U2.unpack(data[index : index + 2])[0] - 1
        ]
        boostrap = class_file.attributes["BootstrapMethods"][0].entries[cp[1]]

        # The type side for the execution
        side = boostrap[0][2][1][1][1]
        return (
            (cp, side, boostrap),
            5,
        )

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        if len(data) != 2:
            raise StackCollectingException(
                f"invalid InvokeDynamic target: target {data[1]} not found!"
            )
        else:
            method, data = data
            # m = stack.vm.get_method_of_nat(data[0])
            call_site = method((data[1][2], data[0], data[1]), data[1][0][2][1][1], data[1][2])
            stack.push(call_site)

    @classmethod
    def optimiser_iteration(
        cls,
        container: "BytecodeRepr",
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


@BytecodeRepr.register_instruction
class LambdaInvokeDynamic(BaseInstruction):
    """
    Class representing the factory system for a lambda
    """

    class LambdaInvokeDynamicWrapper:
        def __init__(
            self, method, name: str, signature: str, extra_args: typing.Iterable
        ):
            self.method = method
            self.name = name
            self.signature = signature
            self.extra_args = extra_args
            self.access = method.access  # access stays the same

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
    def invoke(cls, data: typing.Any, stack: Stack):
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
                extra_args += [stack.pop() for _ in range(inner_args - outer_args)]

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


@BytecodeRepr.register_instruction
class New(CPLinkedInstruction):
    OPCODES = {0xBB}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        c = stack.vm.get_class(
            data[1][1], version=stack.method.class_file.internal_version
        )
        stack.push(c.create_instance())


@BytecodeRepr.register_instruction
class NewArray(CPLinkedInstruction):
    OPCODES = {0xBC}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.Java.U1.unpack(data[index : index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push([None] * stack.pop())


@BytecodeRepr.register_instruction
class ANewArray(CPLinkedInstruction):
    OPCODES = {0xBD}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push([None] * stack.pop())


@BytecodeRepr.register_instruction
class ArrayLength(OpcodeInstruction):
    """
    Resolves the length of an array

    In some contexts, this result is constant in each call
    Can we detect this?
    """

    OPCODES = {0xBE}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(len(stack.pop()))


@BytecodeRepr.register_instruction
class AThrow(OpcodeInstruction):
    """
    Throws an exception

    In some cases, this raise can be moved up some instructions when no side effect is detected
    """

    OPCODES = {0xBF}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        exception = stack.pop()
        stack.stack.clear()
        stack.push(exception)
        raise StackCollectingException("User raised exception", base=exception).add_trace(exception)


@BytecodeRepr.register_instruction
class CheckCast(CPLinkedInstruction):
    OPCODES = {0xC0}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        pass  # todo: implement


@BytecodeRepr.register_instruction
class InstanceOf(CPLinkedInstruction):
    OPCODES = {0xC1}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        obj = stack.pop()

        if not hasattr(obj, "get_class"):
            # todo: we need a fix here!
            stack.push(0)
        else:
            stack.push(int(obj is None or obj.get_class().is_subclass_of(data[1][1])))


@BytecodeRepr.register_instruction
class IfNull(CompareHelper):
    OPCODES = {0xC6}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() is None:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfNonNull(CompareHelper):
    OPCODES = {0xC7}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() is not None:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class Mul(OpcodeInstruction):
    OPCODES = {0x68, 0x6B, 0x6A}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(stack.pop() * stack.pop())


@BytecodeRepr.register_instruction
class NEG(OpcodeInstruction):
    OPCODES = {0x76}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(-stack.pop())


@BytecodeRepr.register_instruction
class TableSwitch(OpcodeInstruction):
    OPCODES = {0xAA}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        initial = index

        while index % 4 != 0:
            index += 1

        default = jvm.Java.pop_u4_s(data[index:])
        index += 4

        low = jvm.Java.pop_u4_s(data[index:])
        index += 4

        high = jvm.Java.pop_u4_s(data[index:])
        index += 4

        offsets = [
            jvm.Java.pop_u4_s(data[index + i * 4 :])
            for i in range(high - low + 1)
        ]
        index += (high - low + 1) * 4
        return (default, low, high, offsets), index - initial

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        index = stack.pop()
        if index < data[1] or index > data[2]:
            stack.cp += data[0]
        else:
            stack.cp += data[3][index - data[1]]
        return True

    @classmethod
    def code_reference_changer(
        cls,
        container: "BytecodeRepr",
        prepared_data: typing.Any,
        instruction_index: int,
        old_index: int,
        checker: typing.Callable[[int], int],
    ):
        default, low, high, offsets = prepared_data
        return checker(default + old_index) - instruction_index, low, high, [checker(e + old_index) - instruction_index for e in offsets]


@BytecodeRepr.register_instruction
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

        while index % 4 != 0:
            index += 1

        default = jvm.Java.pop_u4_s(data[index:])
        index += 4
        npairs = jvm.Java.pop_u4_s(data[index:])
        index += 4

        if npairs > 100:
            logger.println(
                f"unusual high npair count {npairs}. This normally indicates an error in bytecode"
            )
            logger.println(data[index : 40 + index], index)

        try:
            pairs = {
                jvm.Java.pop_u4_s(
                    data
                ): jvm.Java.pop_u4_s(data[index + i * 4 :])
                for i in range(npairs)
            }
            index += npairs * 4
        except:
            raise StackCollectingException(
                f"during decoding lookupswitch of {npairs} entries, defaulting to {default}"
            )

        return (default, pairs), index - before + 1

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        key = stack.pop()

        if key not in data[1]:
            stack.cp += data[0]
        else:
            stack.cp += data[0][key]

        return True

    @classmethod
    def code_reference_changer(
        cls,
        container: "BytecodeRepr",
        prepared_data: typing.Any,
        instruction_index: int,
        old_index: int,
        checker: typing.Callable[[int], int],
    ):
        default, pairs = prepared_data
        return checker(default + old_index) - instruction_index, {e[0]: checker(e[1] + old_index) - instruction_index for e in pairs.items()}
