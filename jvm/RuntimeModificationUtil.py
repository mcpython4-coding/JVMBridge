import typing

import jvm.Instructions


class AbstractCodeModifier:
    MUST_CHECK_DIRECT_AFTER = False

    def walk(self, container):
        raise NotImplementedError


class CodeSingleInstructionHitModifier(AbstractCodeModifier):
    def __init__(self, code_type, injector: typing.Callable, checker: typing.Callable = None, checks=-1, offset=0):
        """
        Creates a new code walker object modifying a single instruction
        Contains some configuration options
        :param code_type: the instruction to manipulate, must be class
        :param injector: a method taking the container and a instruction index, modifying the code object
        :param checker: a method, optional, to validate one occurs
        :param checks: how many to modify, -1 for all, excluding skipped ones
        :param offset: a offset, in hits from method head
        """
        self.code_type = code_type
        self.injector = injector
        self.checker = checker
        self.checks = checks
        self.offset = offset

    def walk(self, container):
        pending_hits = self.offset
        hits = 0

        for i, e in enumerate(container.decoded_code):
            if e is None:
                continue

            if e[0] == self.code_type:
                if self.checker is None or self.checker(container, i):
                    if pending_hits > 0:
                        pending_hits -= 1
                    else:
                        hits += 1
                        self.injector(container, i)

                        # this means we have set a hit limit and it is reached
                        if hits > self.checks >= 0:
                            return


class InvokeInstructionMatcher:
    """
    Helper class for targeting a defined InvokeXY instruction

    Can be put into the checker parameter of a code modifier
    """

    def __init__(self, class_name: str, method_name: str, signature: str):
        self.class_name = class_name
        self.method_name = method_name
        self.signature = signature

    def __call__(self, container, address: int) -> bool:
        instruction = container.decoded_code[address][1]

        return instruction[1][1][1] == self.class_name and instruction[2][1][1] == self.method_name and instruction[2][2][1] == self.signature


def create_method_relocator(address_in: typing.Tuple[str, str, str], address_out: typing.Tuple[str, str, str], ground_type=None, target_type=None, **config):
    """
    Creates a modifier object relocating all method calls to a function to another function
    """
    import jvm.Runtime
    matcher = InvokeInstructionMatcher(*address_in)

    def inject_method(container: jvm.Runtime.BytecodeRepr, address: int):
        container.decoded_code[address] = (jvm.Instructions.InvokeVirtual if target_type is not None else target_type, [10, [7, [1, address_out[0]]], [12, [1, address_out[1]], [1, address_out[2]]]], 3)

    return CodeSingleInstructionHitModifier(jvm.Instructions.InvokeVirtual if ground_type is None else ground_type, inject_method, checker=matcher, **config)

