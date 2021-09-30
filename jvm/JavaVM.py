import typing

from jvm.api import AbstractJavaVM

from jvm.natives import manager as native_manager
from jvm.api import DYNAMIC_NATIVES
from jvm.logging import info
from jvm.Java import JavaArrayManager
from jvm.Java import JavaBytecodeClass
from jvm.JavaExceptionStack import StackCollectingException
import jvm.api
from jvm.api import AbstractJavaClass
from jvm.native_building import dumpClassCreationToFiles


# And this can be wrapped into your own resource access (multiple directories, web download, whatever you want)
# (Mcpython wraps it around the general resource access implementation called ResourceLoader)
def get_bytecode_of_class(class_name: str):
    with open("./" + class_name.replace(".", "/") + ".class", mode="rb") as f:
        return f.read()


class JavaVM(AbstractJavaVM):
    """
    The java VM, as specified by https://docs.oracle.com/javase/specs/index.html

    Currently, only java bytecode below (and including) java 16 can be loaded

    The JVM is capable of providing non-bytecode classes via the Native system (or for really fancy work,
    own AbstractJavaClass implementations)

    The default implementation for java bytecode is located in this file
    It loads the bytecode as outlined by above document of oracle
    """

    def __init__(self):
        self.debugged_methods = set()
        self.shared_classes: typing.Dict[
            str, typing.Union[AbstractJavaClass, typing.Type]
        ] = {}
        self.classes_by_version: typing.Dict[
            typing.Hashable, typing.Dict[str, AbstractJavaClass]
        ] = {}
        self.lazy_classes: typing.Set[typing.Tuple[typing.Any, str]] = set()

        self.array_helper = JavaArrayManager(self)

        self.simulation = False

    def walk_across_classes(self) -> typing.Iterator[AbstractJavaClass]:
        yield from self.shared_classes.values()
        for l in self.classes_by_version.values():
            yield from l.values()

    def load_lazy(self):
        while len(self.lazy_classes) > 0:
            version, name = self.lazy_classes.pop()
            self.get_class(name, version=version)

    def get_class(self, name: str, version=0) -> typing.Optional[AbstractJavaClass]:
        """
        Looks up a specific class in the internal class loader array, and loads it from bytecode if not arrival
        :param name: the name of the class
        :param version: the version to load in, as like a "ClassLoader" instance
        :return: the class, or None on some error
        """

        if self.simulation: return

        name = name.replace(".", "/")

        # Is the name L...;?
        if name.endswith(";") and not name.startswith("["):
            name = name[1:-1]

        if name in self.shared_classes:
            cls = self.shared_classes[name]
        elif name in self.classes_by_version.setdefault(version, {}):
            cls = self.classes_by_version[version][name]
        else:
            cls = self.load_class(name, version=version)

        cls.prepare_use()

        return cls

    def get_lazy_class(self, name: str, version: typing.Any = 0):
        name = name.replace(".", "/")

        if name not in self.shared_classes and name not in self.classes_by_version.setdefault(version, {}):
            self.lazy_classes.add((version, name))

        return lambda: self.get_class(name, version=version)

    def load_class(
        self, name: str, version: typing.Any = 0, shared=False
    ) -> AbstractJavaClass:
        name = name.replace(".", "/")
        if name.startswith("["):
            return self.array_helper.get(name, version=version)

        try:
            bytecode = get_bytecode_of_class(name)
        except FileNotFoundError:
            if DYNAMIC_NATIVES:
                return self.create_native(name, version)

            raise StackCollectingException(f"class file source for '{name}' not found!").add_trace(f"class loader version annotation: {version}") from None

        return self.load_class_from_bytecode(name, bytecode, version=version, shared=shared)

    def create_native(self, name: str, version):
        head = native_manager.get_header_for_cls(name)

        if head is None:
            raise StackCollectingException(f"class file source for '{name}' not found!").add_trace(
                f"class loader version annotation: {version}") from None

        cls = head.create_class(name)
        self.shared_classes[name] = cls
        return cls

    def load_class_from_bytecode(self, name: str, bytecode: bytes, version=None, shared=False, prepare=True):
        info("loading java class '" + name + "'")

        cls = JavaBytecodeClass()
        cls.internal_version = version
        cls.vm = self

        try:
            cls.from_bytes(bytearray(bytecode))
        except StackCollectingException as e:
            e.add_trace(f"decoding class {name}")
            raise

        if prepare:
            if not shared:
                self.classes_by_version.setdefault(version, {})[name] = cls
            else:
                self.shared_classes[name] = cls

            try:
                cls.bake()
                cls.validate_class_file()
            except StackCollectingException as e:
                e.add_trace(f"baking class {name}")
                raise

        info(f"class load of class '{name}' finished")

        return cls

    def register_direct(self, cls: jvm.api.AbstractJavaClass):
        version = cls.internal_version

        if version is None:
            self.shared_classes[cls.name] = cls
        else:
            self.classes_by_version.setdefault(version, {})[cls.name] = cls

    def register_special(self, cls: jvm.api.AbstractJavaClass, name: str, version=...):
        version = cls.internal_version if version is ... else version

        if version is None:
            self.shared_classes[name] = cls
        else:
            self.classes_by_version.setdefault(version, {})[name] = cls

    def get_method_of_nat(self, nat, version: typing.Any = 0):
        cls = nat[1][1][1]
        name = nat[2][1][1]
        descriptor = nat[2][2][1]
        cls = self.get_class(cls, version=version)
        return cls.get_method(name, descriptor)

    def debug_method(self, cls: str, name: str, sig: str):
        self.debugged_methods.add((cls, name, sig))


jvm.api.vm = JavaVM()
# jvm.api.vm.debug_method("com/enderio/core/client/handlers/ClientHandler", "onClientTick", "(Lnet/minecraftforge/fml/common/gameevent/TickEvent$ClientTickEvent;)V")
# jvm.api.vm.debug_method("com/enderio/core/common/handlers/FireworkHandler", "onPlayerTick", "(Lnet/minecraftforge/fml/common/gameevent/TickEvent$PlayerTickEvent;)V")

