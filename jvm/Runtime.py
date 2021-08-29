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
import copy
import sys
import typing
from abc import ABC
import array

import jvm.Java
import jvm.JavaAttributes
import jvm.logging
import jvm.util
from jvm.JavaExceptionStack import StackCollectingException
import jvm.RuntimeModificationUtil

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
            from mcpython.common.mod.util import LoadingInterruptException

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

    @classmethod
    def get_arg_parts_of(
        cls,
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
                f"StackUnderflowException during preparing method execution of '{method}' (static: {static}) with stack size before data popping {previous_count}, expecting {len(parts)+(int(not static))} ({parts})"
            )
            raise

        if isinstance(method, jvm.Java.JavaMethod):
            offset = 0
            for i, (_, state) in enumerate(parts):
                if state:
                    args.insert(i + offset - 1, None)
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
            jvm.logging.warn(f"launching method {self.method} with local vars {self.local_vars}")

        while self.cp != -1:
            instruction = self.code.decoded_code[self.cp]

            if instruction is None:
                next_below = None
                for i in range(self.cp, -1, -1):
                    if self.code.decoded_code[i] is not None:
                        next_below = self.code.decoded_code[i]
                        break

                raise StackCollectingException(
                    "Instruction jump target was invalid [null -> inside instruction data]"
                ).add_trace(f"during fetching {self.cp} in {self.method}").add_trace(
                    f"next below: {next_below}"
                )

            if debugging:
                jvm.logging.warn(
                    "instruction [info before invoke] " + str((self.cp, instruction))
                )
                jvm.logging.warn(
                    f"stack ({len(self.stack)}): " + str(self.stack)[-300:]
                )
                jvm.logging.warn(
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
                if isinstance(self.method, jvm.Java.JavaMethod):
                    self.method.print_stats()
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
            jvm.logging.warn(
                ("finished method", self.method, self.return_value)
            )


class VirtualStack:
    def __init__(self):
        self.stack = []
        self.cp = 0
        self.previous_visited = set()
        self.pending = []
        
    def push(self, data_type=None):
        self.stack.append(data_type)
        
    def pop(self):
        if len(self.stack) == 0:
            raise StackCollectingException("StackUnderflowException detected")
        return self.stack.pop(-1)
    
    def pop_expect_type(self, *type_name: str):
        t = self.stack.pop(-1)
        if t is None or t in type_name:
            return t
        raise StackCollectingException("invalid stack type")
    
    def visit(self):
        self.previous_visited.add((self.cp, tuple(self.stack)))
        
    def branch(self, offset):
        self.pending.append((self.cp+offset, self.stack.copy()))
        
    def check(self) -> bool:
        return (self.cp, tuple(self.stack)) in self.previous_visited


class BaseInstruction(ABC):
    """
    Every instruction has to implement this, everything else does not matter
    """

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        raise NotImplementedError

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        pass
    
    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
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

    MODIFICATION_ITERATIONS = []

    def __init__(self, code: jvm.JavaAttributes.CodeParser):
        self.code = code

        self.decoded_code: typing.List[
            typing.Optional[typing.Tuple[OpcodeInstruction, typing.Any, int]]
        ] = [None] * len(code.code)

        # todo: use to indicate if bytecodes are jump-targets for optimisation lookup
        # self.is_jump_target = array.ArrayType("b")

        code = bytearray(code.code)
        i = 0
        while 0 <= i < len(code):
            tag = code[i]

            if tag in self.OPCODES:
                instr = self.OPCODES[tag]

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

        for modifier in self.MODIFICATION_ITERATIONS:
            modifier.walk(self)

            if modifier.MUST_CHECK_DIRECT_AFTER:
                self.validate_code()

        self.validate_code()

    def validate_code(self):
        """
        Helper method for validating the internal bytecode state and its assigned data
        It first validates the base instructions via the validate() call and than does some code
        stack simulation to validate the stack integrity over the runtime.
        """

        self.validate_code_data()
        self.validate_runtime_stack()

    def validate_code_data(self):
        """
        Helper method for validating the assigned data of all assigned instructions
        """

        for i, e in enumerate(self.decoded_code):
            if e is None:
                continue

            try:
                e[0].validate(i, e[1], self)
            except StackCollectingException as x:
                self.print_stats()
                x.add_trace(
                    f"during validating {e[0].__name__} with data {e[1]} stored at index {i} in {self.code.table.parent}"
                )
                raise

    def validate_runtime_stack(self):
        """
        Simulates an execution in all arrival paths without real execution. Simulates stack pop's/push's for most
        instructions [InvokeDynamic currently is not working]
        """

        # the virtual stack to execute on
        stack = VirtualStack()

        # As long as there are arrival paths, we need to work
        while True:
            # as long as the current path is finished, fetch a new one, and when there is none, exit the method
            while not stack.check():
                if len(stack.pending) == 0: return

                stack.cp, stack.stack = stack.pending.pop(0)

            # prepare for similuation
            prev_cp = stack.cp
            e = self.decoded_code[stack.cp]

            # try simulating it
            try:
                e[0].validate_stack(stack.cp, e[1], self, stack)
            except StackCollectingException as x:
                # and add meta information when it fails
                self.print_stats()
                x.add_trace(
                    f"during validating stack operations on {e[0].__name__} with data {e[1]} stored at index {stack.cp} in {self.code.table.parent}"
                )
                raise

            if prev_cp == stack.cp:
                stack.cp += e[2]

            stack.visit()

    def print_stats(self):
        print(f"ByteCodeRepr stats of {self}")
        print(f"code entries: {len(self.decoded_code)}")
        for i, e in enumerate(self.decoded_code):
            if e is not None:
                print(f" - {i}: {e[0].__name__}({repr(e[1]).removeprefix('(').removesuffix(')')})")

    def exchange_jump_offsets(self, begin_section: int, end_section: int, replace_section: typing.List, reference_reworker=lambda address, start, old_end, new_end: 0):
        """
        Helper method for exchanging two section of code with a new one and re-resolving references
        :param begin_section: where the section begins
        :param end_section: where the section ends
        :param replace_section: what the section should be replaced without
        :param reference_reworker: a callable taking an address and the section parameters and should return the new pointer

        todo: add a "builder" variant taking multiple changes, chaining them together and applying reference changes at ones
        """

        self.decoded_code = self.decoded_code[:begin_section] + replace_section + self.decoded_code[end_section:]
        new_end = begin_section + len(replace_section)

        # This method re-references the references in the instructions
        def resolve(address: int):
            if address < begin_section: return address
            if address > end_section: return address - end_section + new_end
            return reference_reworker(address, begin_section, end_section, new_end)

        # Iterate over all code and do the stuff
        for i, instruction in enumerate(self.decoded_code):
            if instruction is None: continue
            new_data = instruction[0].code_reference_changer(self, instruction[1], i, i if i < new_end else i - new_end + end_section, resolve)
            if new_data is None: continue
            self.decoded_code[i] = (instruction[0], new_data) + instruction[2:]

    def prepare_stack(self, stack: Stack):
        """
        Helper method for setting up the stack for execution of this code block

        todo: do some more stuff here
        """
        stack.local_vars = [None] * self.code.max_locals
        stack.cp = 0
        stack.code = self


# Now, the instruction implementations


@BytecodeRepr.register_instruction
class NoOp(OpcodeInstruction):
    # NoOp
    OPCODES = {0x00}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        pass


@BytecodeRepr.register_instruction
class NoOpPop(OpcodeInstruction):
    # C2 and C3: monitor stuff, as we are not threading, this works as it is
    OPCODES = {0xC2, 0xC3}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.pop()

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()


@BytecodeRepr.register_instruction
class Any2Byte(OpcodeInstruction):
    # i2b
    OPCODES = {0x91}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        v = stack.pop()
        stack.push(int(v) if v is not None else v)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()
        stack.push("B")


@BytecodeRepr.register_instruction
class Any2Float(OpcodeInstruction):
    # i2f, d2f
    OPCODES = {0x86, 0x90}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        v = stack.pop()
        stack.push(float(v) if v is not None else v)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()
        stack.push("F")


@BytecodeRepr.register_instruction
class Any2Double(Any2Float):
    # i2d, f2d, l2d
    OPCODES = {0x87, 0x8D, 0x8A}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()
        stack.push("D")


@BytecodeRepr.register_instruction
class Any2Int(OpcodeInstruction):
    # d2i, f2i, l2i
    OPCODES = {0x8E, 0x8B, 0x88}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        v = stack.pop()
        stack.push(int(v) if v is not None else v)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()
        stack.push("I")


@BytecodeRepr.register_instruction
class Any2Long(Any2Int):
    # f2l
    OPCODES = {0x8C, 0x85}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()
        stack.push("J")


class ConstPush(OpcodeInstruction, ABC):
    """
    Base class for instructions pushing pre-defined objects
    """

    PUSHES = None
    PUSH_TYPE = None

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(cls.PUSHES)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.push(cls.PUSH_TYPE)


@BytecodeRepr.register_instruction
class AConstNull(ConstPush):
    OPCODES = {0x01}
    PUSH_TYPE = "null"


@BytecodeRepr.register_instruction
class IConstM1(ConstPush):
    OPCODES = {0x02}
    PUSHES = -1
    PUSH_TYPE = "i"


@BytecodeRepr.register_instruction
class IConst0(ConstPush):
    OPCODES = {0x03}
    PUSHES = 0
    PUSH_TYPE = "i"


@BytecodeRepr.register_instruction
class LConst0(ConstPush):
    OPCODES = {0x09}
    PUSHES = 0
    PUSH_TYPE = "j"


@BytecodeRepr.register_instruction
class DConst0(ConstPush):
    OPCODES = {0x0E}
    PUSHES = 0
    PUSH_TYPE = "d"


@BytecodeRepr.register_instruction
class IConst1(ConstPush):
    OPCODES = {0x04}
    PUSHES = 1
    PUSH_TYPE = "i"


@BytecodeRepr.register_instruction
class DConst1(ConstPush):
    OPCODES = {0x0F}
    PUSHES = 1
    PUSH_TYPE = "d"


@BytecodeRepr.register_instruction
class IConst2(ConstPush):
    OPCODES = {0x05}
    PUSHES = 2
    PUSH_TYPE = "i"


@BytecodeRepr.register_instruction
class IConst3(ConstPush):
    OPCODES = {0x06}
    PUSHES = 3
    PUSH_TYPE = "i"


@BytecodeRepr.register_instruction
class IConst4(ConstPush):
    OPCODES = {0x07}
    PUSHES = 4
    PUSH_TYPE = "i"


@BytecodeRepr.register_instruction
class IConst5(ConstPush):
    OPCODES = {0x08}
    PUSHES = 5
    PUSH_TYPE = "i"


@BytecodeRepr.register_instruction
class LConst0(ConstPush):
    OPCODES = {0x09}
    PUSHES = 0
    PUSH_TYPE = "j"


@BytecodeRepr.register_instruction
class LConst1(ConstPush):
    OPCODES = {0x0A}
    PUSHES = 1
    PUSH_TYPE = "j"


@BytecodeRepr.register_instruction
class FConst0(ConstPush):
    OPCODES = {0x0B}
    PUSHES = 0.0
    PUSH_TYPE = "f"


@BytecodeRepr.register_instruction
class FConst1(ConstPush):
    OPCODES = {0x0C}
    PUSHES = 1.0
    PUSH_TYPE = "f"


@BytecodeRepr.register_instruction
class FConst2(ConstPush):
    OPCODES = {0x0D}
    PUSHES = 2.0
    PUSH_TYPE = "f"


@BytecodeRepr.register_instruction
class BiPush(OpcodeInstruction):
    OPCODES = {0x10}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U1_S.unpack(data[index: index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(data)
        
    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.push("B")


@BytecodeRepr.register_instruction
class SiPush(OpcodeInstruction):
    OPCODES = {0x11}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U2_S.unpack(data[index: index + 2])[0], 3

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(data)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.push("S")


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
            jvm.util.decode_cp_constant(
                stack.method.class_file.cp[data - 1],
                version=stack.method.class_file.internal_version,
            )
        )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.push(None)  # todo: add type


@BytecodeRepr.register_instruction
class LDC_W(OpcodeInstruction):
    OPCODES = {0x13, 0x14}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U2.unpack(data[index: index + 2])[0], 3

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(
            jvm.util.decode_cp_constant(
                stack.method.class_file.cp[data - 1],
                version=stack.method.class_file.internal_version,
            )
        )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.push(None)  # todo: add type


@BytecodeRepr.register_instruction
class ArrayLoad(OpcodeInstruction):
    OPCODES = {0x32, 0x2E, 0x33, 0x31}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        index = stack.pop()
        array = stack.pop()

        if index is None:
            raise StackCollectingException("NullPointerException: index is null")

        if array is None:
            raise StackCollectingException("NullPointerException: array is null")

        stack.push(array[index])
        
    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop_expect_type("i", "j")
        stack.pop()
        stack.push(None)  # todo: add type here


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

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.pop()
        stack.pop_expect_type("i", "j")
        stack.pop()


@BytecodeRepr.register_instruction
class Load(OpcodeInstruction):
    OPCODES = {0x19, 0x15, 0x18, 0x17, 0x16}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U1.unpack(data[index: index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(stack.local_vars[data])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        if prepared_data >= container.code.max_locals:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: {prepared_data} does not fit into {container.code.max_locals}"
            )
        
    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.push(None)


@BytecodeRepr.register_instruction
class Load0(OpcodeInstruction):
    OPCODES = {0x2A, 0x1A, 0x22, 0x26, 0x1E}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(stack.local_vars[0])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 0:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 0 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.push(None)


@BytecodeRepr.register_instruction
class Load1(OpcodeInstruction):
    OPCODES = {0x2B, 0x1B, 0x23, 0x27, 0x1F}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(stack.local_vars[1])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 1:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 1 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.push(None)


@BytecodeRepr.register_instruction
class Load2(OpcodeInstruction):
    OPCODES = {0x2C, 0x1C, 0x24, 0x28, 0x20}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(stack.local_vars[2])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 2:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 2 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.push(None)


@BytecodeRepr.register_instruction
class Load3(OpcodeInstruction):
    OPCODES = {0x2D, 0x1D, 0x25, 0x29, 0x21}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(stack.local_vars[3])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 3:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 3 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.push(None)


@BytecodeRepr.register_instruction
class Store(OpcodeInstruction):
    OPCODES = {0x3A, 0x36, 0x39, 0x38, 0x37}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U1.unpack(data[index: index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[data] = stack.pop()

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        if prepared_data >= container.code.max_locals:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: {prepared_data} does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.pop()


@BytecodeRepr.register_instruction
class Store0(OpcodeInstruction):
    OPCODES = {0x4B, 0x3B, 0x47, 0x43, 0x3F}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[0] = stack.pop()

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 0:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 0 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.pop()


@BytecodeRepr.register_instruction
class Store1(OpcodeInstruction):
    OPCODES = {0x4C, 0x3C, 0x48, 0x44, 0x40}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[1] = stack.pop()

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 1:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 1 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.pop()


@BytecodeRepr.register_instruction
class Store2(OpcodeInstruction):
    OPCODES = {0x4D, 0x3D, 0x49, 0x45, 0x41}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[2] = stack.pop()

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 2:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 2 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.pop()


@BytecodeRepr.register_instruction
class Store3(OpcodeInstruction):
    OPCODES = {0x4E, 0x3E, 0x4A, 0x46, 0x42}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[3] = stack.pop()

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        if container.code.max_locals <= 3:
            raise StackCollectingException(
                f"LocalVariableIndexOutOfBounds: 3 does not fit into {container.code.max_locals}"
            )

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.pop()


@BytecodeRepr.register_instruction
class POP(OpcodeInstruction):
    OPCODES = {0x57}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.pop()

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr",
                       stack: VirtualStack):
        stack.pop()


@BytecodeRepr.register_instruction
class DUP(OpcodeInstruction):
    OPCODES = {0x59}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        v = stack.pop()
        stack.push(v)
        stack.push(v)
        
    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        t = stack.pop()
        stack.push(t)
        stack.push(t)


@BytecodeRepr.register_instruction
class DUP_X1(OpcodeInstruction):
    OPCODES = {0x5A}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        a, b = stack.pop(), stack.pop()
        stack.push(a)
        stack.push(b)
        stack.push(a)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
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

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)


@BytecodeRepr.register_instruction
class SUB(OpcodeInstruction):
    OPCODES = {0x66, 0x64, 0x67}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(b - a)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)


@BytecodeRepr.register_instruction
class IDIV(OpcodeInstruction):
    OPCODES = {0x6C}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a // b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)


@BytecodeRepr.register_instruction
class FDIV(OpcodeInstruction):
    OPCODES = {0x6E, 0x6F}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a / b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)


@BytecodeRepr.register_instruction
class SHL(OpcodeInstruction):
    OPCODES = {0x78}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a << b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)


@BytecodeRepr.register_instruction
class SHR(OpcodeInstruction):
    OPCODES = {0x7A}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a >> b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)


@BytecodeRepr.register_instruction
class AND(OpcodeInstruction):
    OPCODES = {0x7E}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a & b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)


@BytecodeRepr.register_instruction
class OR(OpcodeInstruction):
    OPCODES = {0x80}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        b, a = stack.pop(), stack.pop()
        stack.push(a | b)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        a = stack.pop()
        stack.pop_expect_type(a)
        stack.push(a)


@BytecodeRepr.register_instruction
class IINC(OpcodeInstruction):
    OPCODES = {0x84}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return (
                   data[index],
                   jvm.util.U1_S.unpack(data[index + 1: index + 2])[0],
        ), 3

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.local_vars[data[0]] += data[1]

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        if prepared_data[0] >= container.code.max_locals:
            raise StackCollectingException(f"local var index {prepared_data[0]} out of range")


class CompareHelper(OpcodeInstruction, ABC):
    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U2_S.unpack(data[index: index + 2])[0], 3

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

    @classmethod
    def validate(cls, command_index: int, prepared_data: typing.Any, container: "BytecodeRepr"):
        if command_index + prepared_data < 0:
            raise StackCollectingException(f"opcode index {command_index + prepared_data} is < 0 (OutOfBoundError)")
        elif command_index + prepared_data >= len(container.decoded_code):
            raise StackCollectingException(f"opcode index {command_index + prepared_data} is >= {len(container.decoded_code)} (OutOfBoundError)")
        elif container.decoded_code[command_index + prepared_data] is None:
            raise StackCollectingException(f"opcode index {command_index+prepared_data} is pointing into opcode BODY, not HEAD (bound 0 <= {command_index+prepared_data} < {len(container.decoded_code)})")


class SingleCompare(CompareHelper, ABC):
    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()
        stack.branch(prepared_data)


class DoubleCompare(CompareHelper, ABC):
    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()
        stack.pop()
        stack.branch(prepared_data)


@BytecodeRepr.register_instruction
class IfLT(DoubleCompare):
    OPCODES = {0x97}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() > stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfGT(DoubleCompare):
    OPCODES = {0x98}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() < stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfEq0(SingleCompare):
    OPCODES = {0x99}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() == 0:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfNEq0(SingleCompare):
    OPCODES = {0x9A}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() != 0:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfLT0(SingleCompare):
    OPCODES = {0x9B}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() < 0:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfGE0(SingleCompare):
    OPCODES = {0x9C}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() >= 0:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfGT0(SingleCompare):
    OPCODES = {0x9D}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() > 0:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfLE0(SingleCompare):
    OPCODES = {0x9E}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() <= 0:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfEq(DoubleCompare):
    OPCODES = {0x9F}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() == stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfNE(DoubleCompare):
    OPCODES = {0xA0}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() != stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfLt(DoubleCompare):
    OPCODES = {0xA1}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() > stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfGe(DoubleCompare):
    OPCODES = {0xA2}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() <= stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfLe(DoubleCompare):
    OPCODES = {0xA4}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() >= stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfEq(DoubleCompare):
    OPCODES = {0xA5}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() == stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfNEq(DoubleCompare):
    OPCODES = {0xA6}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() != stack.pop():
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class Goto(CompareHelper):
    OPCODES = {0xA7}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.cp += data
        return True

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.cp += prepared_data


@BytecodeRepr.register_instruction
class AReturn(OpcodeInstruction):
    OPCODES = {0xB0, 0xAC, 0xAE}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.end(stack.pop())

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()
        stack.cp = -1


@BytecodeRepr.register_instruction
class Return(OpcodeInstruction):
    OPCODES = {0xB1}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.end()

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.cp = -1


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

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.push(None)


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

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()


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
            stack.push(obj.get_field(name))
        except (KeyError, AttributeError):
            try:
                stack.push(getattr(obj, name))
            except (KeyError, AttributeError):
                raise StackCollectingException(
                    f"AttributeError: object {obj} (type {type(obj)}) has no attribute {name}"
                ) from None

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.push(None)


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

        if not hasattr(obj, "set_field"):
            setattr(obj, name, value)
        else:
            obj.set_field(name, value)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()


@BytecodeRepr.register_instruction
class InvokeVirtual(CPLinkedInstruction):
    OPCODES = {0xB6}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        # todo: lookup signature and insert here
        args = len(tuple(Runtime.get_arg_parts_of(prepared_data[2][2][1])))
        [stack.pop() for _ in range(args + 1)]
        stack.push(None)

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

        stack.push(stack.runtime.run_method(method, *args))


@BytecodeRepr.register_instruction
class InvokeSpecial(CPLinkedInstruction):
    OPCODES = {0xB7}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        arg_types = tuple(Runtime.get_arg_parts_of(prepared_data[2][2][1]))
        args = len(arg_types)
        [stack.pop_expect_type(arg_types[i]) for i in range(args + 1)]

        if prepared_data[2][1][1] not in (
            "<init>",
            "<clinit>",
        ):
            stack.push(None)

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        method = stack.vm.get_method_of_nat(
            data, version=stack.method.class_file.internal_version
        )
        result = stack.runtime.run_method(
            method, *stack.runtime.parse_args_from_stack(method, stack)
        )
        method_name = (method.name if hasattr(method, "name") else method.native_name)
        if method_name not in (
            "<init>",
            "<clinit>",
        ):
            stack.push(result)


@BytecodeRepr.register_instruction
class InvokeStatic(CPLinkedInstruction):
    OPCODES = {0xB8}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        # todo: lookup signature and insert here
        args = len(tuple(Runtime.get_arg_parts_of(prepared_data[2][2][1])))
        [stack.pop() for _ in range(args)]
        stack.push(None)

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
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
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
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
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

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.cp = -1  # todo: implement

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


@BytecodeRepr.register_instruction
class New(CPLinkedInstruction):
    OPCODES = {0xBB}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.push(None)

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
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop_expect_type("i", "j")
        stack.push(None)

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return jvm.util.U1.unpack(data[index: index + 1])[0], 2

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push([None] * stack.pop())


@BytecodeRepr.register_instruction
class ANewArray(CPLinkedInstruction):
    OPCODES = {0xBD}

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop_expect_type("i", "j")
        stack.push(None)

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
        a = stack.pop()

        if a is None:
            raise StackCollectingException("array is None")

        stack.push(len(a))

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()
        stack.push("i")


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

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()
        stack.cp = -1


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

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()
        stack.push("Z")


@BytecodeRepr.register_instruction
class MultiANewArray(OpcodeInstruction):
    OPCODES = {0xC5}

    @classmethod
    def decode(
        cls, data: bytearray, index, class_file
    ) -> typing.Tuple[typing.Any, int]:
        return (data[index:index+2], data[index+2]), 4

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        dimensions = [stack.pop() for _ in range(data[1])]
        data = [None] * dimensions.pop(0)

        for e in dimensions:
            data = [copy.deepcopy(data) for _ in range(e)]

        stack.push(data)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        for _ in range(prepared_data[1]):
            stack.pop_expect_type("i", "j")
        stack.push(None)


@BytecodeRepr.register_instruction
class IfNull(SingleCompare):
    OPCODES = {0xC6}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        if stack.pop() is None:
            stack.cp += data
            return True


@BytecodeRepr.register_instruction
class IfNonNull(SingleCompare):
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

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        t = stack.pop()
        stack.pop_expect_type(t)
        stack.push(t)


@BytecodeRepr.register_instruction
class NEG(OpcodeInstruction):
    OPCODES = {0x76}

    @classmethod
    def invoke(cls, data: typing.Any, stack: Stack):
        stack.push(-stack.pop())

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        t = stack.pop()
        stack.push(t)


@BytecodeRepr.register_instruction
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
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
        index = stack.pop()

        if index < data[1] or index > data[2]:
            stack.cp += data[0]
        else:
            stack.cp += data[3][index - data[1]]

        return True

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()

        for offset in prepared_data[3]:
            stack.branch(offset)

        stack.cp += prepared_data[0]

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
        return checker(default + old_index) - instruction_index, low, high, array.ArrayType("l", [checker(e + old_index) - instruction_index for e in offsets])

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        for offset in prepared_data[3]:
            CompareHelper.validate(command_index, offset, container)
        CompareHelper.validate(command_index, prepared_data[0], container)


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
    def invoke(cls, data: typing.Any, stack: Stack) -> bool:
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
        container: "BytecodeRepr",
        prepared_data: typing.Any,
        instruction_index: int,
        old_index: int,
        checker: typing.Callable[[int], int],
    ):
        default, pairs = prepared_data
        return checker(default + old_index) - instruction_index, {e[0]: checker(e[1] + old_index) - instruction_index for e in pairs.items()}

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr"):
        for offset in prepared_data[1].values():
            CompareHelper.validate(command_index, offset, container)

        CompareHelper.validate(command_index, prepared_data[0], container)

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: "BytecodeRepr", stack: VirtualStack):
        stack.pop()

        for offset in prepared_data[1].values():
            stack.branch(offset)

        # the default offset goes here...
        stack.cp += prepared_data[0]
