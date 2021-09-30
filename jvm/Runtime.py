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

import jvm.Java
import jvm.api
import jvm.JavaAttributes
import jvm.logging
import jvm.util
from jvm.api import AbstractBytecodeContainer
from jvm.api import AbstractStack, AbstractRuntime
from jvm.JavaExceptionStack import StackCollectingException
import jvm.RuntimeModificationUtil
from jvm.api import BaseInstruction

DEBUG = "--debug-vm" in sys.argv


class Runtime(AbstractRuntime):
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

    def run_method(self, method: typing.Union[jvm.Java.JavaMethod, typing.Callable], *args, stack=None):
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
            if isinstance(method, jvm.Java.JavaMethod):
                try:
                    code = method.attributes["Code"][0]
                except KeyError:
                    raise StackCollectingException(
                        f"Abstract method call onto {method} with args {args}; Code attribute not found"
                    )
                except AttributeError:
                    if not isinstance(method, jvm.Java.JavaMethod):
                        return method.invoke(args)

                    raise

                method.code_repr = BytecodeRepr(code)
            else:
                return method.invoke(args, stack=stack)

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

        if signature is None:
            raise RuntimeError(method)

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


class Stack(AbstractStack):
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

        history = []

        while self.cp != -1:
            history.append(self.cp)

            if len(history) > 20:
                history.pop(0)

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
                    f"local ({len(self.local_vars)}): " + str(self.local_vars)[:300]
                )

            try:
                result = instruction[0].invoke(instruction[1], self)
            except StackCollectingException as e:
                # This exception MAY be caused by a wrong InvokeDynamic reference (missing static attribute)
                if e.text == "StackUnderflowException":
                    for cp in history:
                        if self.code.decoded_code[cp][0].__name__ == "LambdaInvokeDynamic":
                            e.add_trace(f"after InvokeDynamic on {self.code.decoded_code[cp]}")

                e.add_trace(
                    f"during invoking {instruction[0]} in {self.method} [index: {self.cp}]"
                )
                raise
            except:
                if isinstance(self.method, jvm.Java.JavaMethod):
                    self.method.print_stats(current=self.cp)
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


class VirtualStack(AbstractStack):
    def __init__(self):
        super().__init__()

        self.previous_visited = set()
        self.pending = []

    def seek(self):
        return self.stack[-1]

    def end(self, value):
        self.cp = -1

    def run(self):
        raise RuntimeError
        
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


class BytecodeRepr(AbstractBytecodeContainer):
    """
    Structure storing instruction references and data from loaded methods
    Created moments before first invocation

    Stores all arrival instructions
    """

    MODIFICATION_ITERATIONS = []

    def __init__(self, code: jvm.JavaAttributes.CodeParser):
        super().__init__()

        self.code = code
        self.method: jvm.Java.JavaMethod = code.table.parent

        self.decoded_code: typing.List[
            typing.Optional[typing.Tuple[BaseInstruction, typing.Any, int]]
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

    def print_stats(self, current=None):
        print(f"ByteCodeRepr stats of {self}")
        print(f"code entries: {len(self.decoded_code)}")

        if current is None:
            for i, e in enumerate(self.decoded_code):
                if e is not None:
                    print(f" - {i}: {e[0].__name__}({repr(e[1]).removeprefix('(').removesuffix(')')})")
        else:
            for i, e in enumerate(self.decoded_code):
                if e is not None:
                    if e == current:
                        print(f"-> - {i}: {e[0].__name__}({repr(e[1]).removeprefix('(').removesuffix(')')})")
                    else:
                        print(f"   - {i}: {e[0].__name__}({repr(e[1]).removeprefix('(').removesuffix(')')})")

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

