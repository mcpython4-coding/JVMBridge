import sys
import typing
from abc import ABC
from abc import ABCMeta
from abc import abstractmethod

vm = None


class AbstractRuntime(metaclass=ABCMeta):
    def spawn_stack(self):
        raise NotImplementedError

    def run_method(self, method, *args, stack=None):
        raise NotImplementedError

    @classmethod
    def get_arg_parts_of(cls, method):
        raise NotImplementedError

    def parse_args_from_stack(self, method, stack, static):
        raise NotImplementedError

    def get_current_stack(self):
        raise NotImplementedError


class AbstractStack(metaclass=ABCMeta):
    def __init__(self):
        self.local_vars = []
        self.stack = []

        self.cp = 0

        self.code = None
        self.method = None

        self.vm = vm

        self.runtime: typing.Optional[AbstractRuntime] = None

        self.return_value = None

        self.code: typing.Optional[AbstractBytecodeContainer] = None

    @abstractmethod
    def pop(self):
        pass

    @abstractmethod
    def push(self, value):
        pass

    @abstractmethod
    def seek(self):
        pass

    @abstractmethod
    def end(self, value=None):
        pass

    @abstractmethod
    def run(self):
        """
        Runs the data on this stack
        """
        pass

    def pop_expect_type(self, *type_name: str):
        pass

    def visit(self):
        pass

    def branch(self, offset):
        pass

    def check(self) -> bool:
        pass


class AbstractBytecodeContainer(metaclass=ABCMeta):
    OPCODES: typing.Dict[int, typing.Type["BaseInstruction"]] = {}

    @classmethod
    def register_instruction(cls, instr):
        from jvm.Instructions import OpcodeInstruction

        if issubclass(instr, OpcodeInstruction):
            for opcode in instr.OPCODES:
                cls.OPCODES[opcode] = instr

        return instr

    def __init__(self):
        self.code = None
        self.decoded_code = []

        self.method: typing.Optional[AbstractMethod] = None

    @abstractmethod
    def prepare_stack(self, stack):
        """
        Helper method for setting up the stack for execution of this code block

        todo: do some more stuff here
        """
        pass


class AbstractJavaClass:
    """
    Abstract base class for java classes handled by the vm
    """

    def __init__(self):
        self.name: str = None  # the class name
        self.file_source: str = None  # a path to the file this class was loaded from
        self.parent = None  # the parent of the class
        self.is_public = True
        self.is_final = False
        self.is_special_super = False
        self.is_interface = False
        self.is_abstract = False
        self.is_synthetic = False
        self.is_annotation = False
        self.is_enum = False
        self.is_module = False

        self.interfaces: typing.List[
            typing.Callable[[], typing.Optional[AbstractJavaClass]]
        ] = []
        self.internal_version = None  # the internal version identifier
        self.vm = None  # the vm instance bound to
        self.cp = tuple()

        self.enum_fields = []

    async def get_enum_values(self):
        return [await self.get_static_attribute(e) for e in self.enum_fields]

    async def get_method(self, name: str, signature: str, inner=False):
        raise NotImplementedError

    async def get_static_attribute(self, name: str, expected_type=None):
        raise NotImplementedError

    def set_static_attribute(self, name: str, value, descriptor=None):
        raise NotImplementedError

    async def create_instance(self) -> "AbstractJavaClassInstance":
        raise NotImplementedError

    def inject_method(self, name: str, signature: str, method, force=True):
        raise NotImplementedError

    async def on_annotate(self, obj, args):
        print(f"missing annotation implementation on {self} annotating {obj} with {args}")

    async def get_dynamic_field_keys(self):
        return set()

    def is_subclass_of(self, class_name: str) -> bool:
        raise NotImplementedError

    async def prepare_use(self, runtime=None):
        pass

    def ensure_data(self, data):
        raise RuntimeError("Class does not implement adding data to constant pool")


class AbstractJavaClassInstance(ABC):
    __slots__ = ("fields", "rebound_type")

    def __init__(self):
        self.fields = {}
        self.rebound_type = None

    async def init_fields(self):
        pass

    def get_field(self, name: str):
        raise NotImplementedError

    def set_field(self, name: str, value):
        raise NotImplementedError

    async def get_method(self, name: str, signature: str) -> "AbstractMethod":
        return await (await self.get_class()).get_method(name, signature)

    async def get_class(self) -> AbstractJavaClass:
        return self.rebound_type or self.get_real_class()

    def get_real_class(self) -> AbstractJavaClass:
        raise NotImplementedError

    async def init(self, signature: str, *args, stack=None):
        await (await self.get_method("<init>", signature)).invoke([self]+list(args), stack=stack)
        return self


DYNAMIC_NATIVES = "--fill-unknown-natives" in sys.argv


class AbstractMethod(metaclass=ABCMeta):
    __slots__ = ("class_file", "name", "signature", "access", "code_repr")

    def __init__(self):
        self.class_file: AbstractJavaClass = None
        self.name: str = None
        self.signature: str = None
        self.access = 0
        self.code_repr = None

    @abstractmethod
    async def invoke(self, args, stack=None):
        pass

    @abstractmethod
    def get_parent_class(self):
        pass


class PyBytecodeBuilder:
    def __init__(self):
        self.instruction_sequence = []

    def add_instruction(self, instruction_opcode: int, instruction_data=None):
        pass

    def add_name(self, name: str) -> int:
        pass

    def add_const(self, const):
        pass

    def add_comparator(self, comp: str) -> int:
        pass

    def real_from_offset(self, offset: int) -> int:
        pass


class BaseInstruction(ABC):
    """
    Every instruction has to implement this, everything else does not matter
    """

    @classmethod
    async def invoke(cls, data: typing.Any, stack: AbstractStack) -> bool:
        raise NotImplementedError

    @classmethod
    def validate(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer):
        pass

    @classmethod
    def validate_stack(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, stack: AbstractStack):
        pass

    @classmethod
    async def optimiser_iteration(
        cls,
        container: AbstractBytecodeContainer,
        prepared_data: typing.Any,
        instruction_index: int,
    ):
        pass

    @classmethod
    def code_reference_changer(
        cls,
        container: AbstractBytecodeContainer,
        prepared_data: typing.Any,
        instruction_index: int,
        old_index: int,
        checker: typing.Callable[[int], int],
    ):
        pass

    @classmethod
    def prepare_python_bytecode_instructions(cls, command_index, prepared_data: typing.Any, container: AbstractBytecodeContainer, builder: PyBytecodeBuilder):
        pass

    @classmethod
    def decode(cls, code, index: int, class_file):
        return None, index+1


class AbstractJavaVM(metaclass=ABCMeta):
    @abstractmethod
    async def get_class(self, name, version):
        """
        Looks up a specific class in the internal class loader array, and loads it from bytecode if not arrival
        :param name: the name of the class
        :param version: the version to load in, as like a "ClassLoader" instance
        :return: the class, or None on some error
        """
        pass

    @abstractmethod
    def load_lazy(self):
        pass

    @abstractmethod
    async def get_lazy_class(self, name, version):
        pass

    @abstractmethod
    async def load_class(self, name, version, shared):
        pass

    @abstractmethod
    def register_direct(self, cls):
        pass

    @abstractmethod
    def register_special(self, cls, name, version):
        pass

    @abstractmethod
    def walk_across_classes(self) -> typing.Iterator[AbstractJavaClass]:
        pass
