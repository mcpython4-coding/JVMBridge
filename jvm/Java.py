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

# Framework for loading and executing java bytecode
# Mainly independent from mcpython's source
# See Runtime.py for a system for executing the bytecode
# See builtin folder for python implementations for java internals
import traceback
import typing
import weakref

from jvm.api import AbstractJavaClass
from jvm.api import AbstractJavaClassInstance
from jvm.api import AbstractMethod
from jvm.natives import NativeMethod
from jvm.JavaAttributes import JavaAttributeTable
from jvm.logging import info
from jvm.util import DOUBLE
from jvm.util import FLOAT
from jvm.util import INT
from jvm.util import LONG
from jvm.util import pop_sized
from jvm.util import pop_struct
from jvm.util import pop_u1
from jvm.util import pop_u2
from jvm.util import pop_u4
from jvm.util import U2
from jvm.util import U4
import jvm.api

try:
    from jvm.JavaExceptionStack import StackCollectingException
except ImportError:
    from JavaExceptionStack import StackCollectingException


class ArrayBase(jvm.api.AbstractJavaClass):
    __slots__ = ("attributes", "base_class", "depth", "name")

    def __init__(self, depth: int, name: str, base_class: AbstractJavaClass):
        super().__init__()
        self.methods = {
            ("clone", "()Ljava/lang/Object;"): NativeMethod(self, "clone", "()Ljava/lang/Object;", self.clone)
        }
        self.attributes = {}

        self.base_class = base_class
        self.depth = depth
        self.name = name

    async def get_method(self, name: str, signature: str, inner=False):
        return self.methods[(name, signature)]

    async def get_static_attribute(self, name: str, expected_type=None):
        return self.attributes.setdefault(name, 0)

    def set_static_attribute(self, name: str, value, descriptor=None):
        self.attributes[name] = value

    def inject_method(self, name: str, signature: str, method, force=True):
        self.methods[(name, signature)] = method

    def is_subclass_of(self, class_name: str) -> bool:
        return False

    async def create_instance(self):
        return []

    def clone(self, method, stack, instance):
        return instance.copy() if instance is not None else instance


class JavaArrayManager:
    """
    Helper class for working with java arrays of non-standard type (e.g. [Lnet/minecraft/ResourceLocation;)
    It creates the needed array classes and holds them for later reuse
    """

    __slots__ = ("vm",)

    def __init__(self, vm_i):
        self.vm = weakref.proxy(vm_i)

    async def get(self, class_text: str, version=0):
        depth = class_text.count("[")
        cls_name = class_text[depth:]
        cls = await self.vm.get_class(
            cls_name.removeprefix("L").removesuffix(";"), version=version
        )

        instance = ArrayBase(depth, class_text, cls)

        self.vm.shared_classes[class_text] = instance
        return instance


class JavaField:
    __slots__ = ("class_file", "name", "descriptor", "access", "attributes")

    def __init__(self):
        self.class_file: "JavaBytecodeClass" = None
        self.name: str = None
        self.descriptor: str = None
        self.access = 0
        self.attributes = JavaAttributeTable(self)

    async def from_data(self, class_file: "JavaBytecodeClass", data: bytearray):
        self.class_file = weakref.proxy(class_file)
        self.access = pop_u2(data)
        self.name = class_file.cp[pop_u2(data) - 1][1]
        self.descriptor = class_file.cp[pop_u2(data) - 1][1]
        await self.attributes.from_data(class_file, data)

    def __repr__(self):
        return f"JavaField(name='{self.name}',descriptor='{self.descriptor}',access='{bin(self.access)}',class='{self.class_file.name}')"
    
    def dump(self) -> bytearray:
        data = bytearray()

        data += U2.pack(self.access)
        data += U2.pack(self.class_file.ensure_data([1, self.name]))
        data += U2.pack(self.class_file.ensure_data([1, self.descriptor]))
        data += self.attributes.dump()

        return data


class JavaMethod(AbstractMethod):
    __slots__ = AbstractMethod.__slots__ + ("attributes", "code_repr")

    def __init__(self):
        super().__init__()
        self.attributes = JavaAttributeTable(self)

        self.code_repr = None

    async def ensure_code_repr(self):
        if self.code_repr is not None: return

        from jvm.Runtime import BytecodeRepr
        try:
            code = self.attributes["Code"][0]
        except (KeyError, IndexError):
            return

        self.code_repr = BytecodeRepr(code)
        await self.code_repr.optimiser_iteration()

    async def from_data(self, class_file: "JavaBytecodeClass", data: bytearray):
        self.class_file = weakref.proxy(class_file)
        self.access = pop_u2(data)
        self.name = class_file.cp[pop_u2(data) - 1][1]
        self.signature = class_file.cp[pop_u2(data) - 1][1]
        await self.attributes.from_data(class_file, data)

    def __repr__(self):
        return f"JavaMethod(name='{self.name}',signature='{self.signature}',access='{bin(self.access)}',class='{self.class_file.name}')"

    async def invoke(self, args, stack=None):
        import jvm.Runtime

        runtime = jvm.Runtime.Runtime()
        return await runtime.run_method(self, *args, stack=stack)

    def get_parent_class(self):
        return self.class_file

    async def get_class(self):
        return await self.class_file.vm.get_class(
            "java/lang/reflect/Method", version=self.class_file.internal_version
        )

    async def __call__(self, *args):
        return await self.invoke(args)

    def dump(self) -> bytearray:
        data = bytearray()

        data += U2.pack(self.access)
        data += U2.pack(self.class_file.ensure_data([1, self.name]))
        data += U2.pack(self.class_file.ensure_data([1, self.signature]))
        data += self.attributes.dump()

        return data

    async def print_stats(self, current=None):
        await self.ensure_code_repr()
        print(f"method {repr(self)}")

        if self.code_repr is not None:
            self.code_repr.print_stats(current=current)


def makeStatic(obj):
    if isinstance(obj, list):
        return tuple(makeStatic(e) for e in obj)
    elif isinstance(obj, dict):
        return {key: makeStatic(value) for key, value in obj.items()}
    return obj


class JavaBytecodeClass(AbstractJavaClass):
    def __init__(self):
        super().__init__()
        self.class_file_version = -1, -1

        self.cp: typing.List[typing.Any] = []
        self.access = 0
        self.methods = {}
        self.fields = {}

        self.dynamic_field_keys = set()
        self.static_field_values = {}
        self.attributes = JavaAttributeTable(self)

        self.on_bake = []
        self.on_instance_creation = []

        self.class_init_complete = False

    # todo: add to that object a marker!
    async def on_annotate(self, obj, args):
        pass

    async def from_bytes(self, data: bytearray):
        magic = pop_u4(data)
        assert magic == 0xCAFEBABE, f"magic {magic} is invalid!"

        minor, major = pop_u2(data), pop_u2(data)
        self.class_file_version = major, minor

        info(
            f"class file version: {major}.{minor} (Java {major-44 if major > 45 else '1.0.2 or 1.1'}"
            f"{' preview features enabled' if major > 56 and minor == 65535 else ''})"
        )

        cp_size = pop_u2(data) - 1
        self.cp += [None] * cp_size
        i = 0
        while i < cp_size:
            j = i
            i += 1

            tag = pop_u1(data)

            match tag:
                case 7 | 8 | 16 | 19 | 20:
                    d = tag, pop_u2(data)
                case 9 | 10 | 11 | 12 | 17 | 18:
                    d = tag, pop_u2(data), pop_u2(data)
                case 3:
                    d = tag, pop_struct(INT, data)[0]
                case 4:
                    d = tag, pop_struct(FLOAT, data)[0]
                case 5:
                    d = tag, pop_struct(LONG, data)[0]
                    i += 1
                case 6:
                    d = tag, pop_struct(DOUBLE, data)[0]
                    i += 1
                case 1:
                    size = pop_u2(data)
                    e = pop_sized(size, data)
                    d = tag, e.decode("utf-8", errors="ignore")
                case 15:
                    d = tag, pop_u1(data), pop_u2(data)
                case _:
                    raise ValueError(tag)

            self.cp[j] = list(d)

        for i, e in enumerate(self.cp):
            if e is None:
                continue

            tag = e[0]

            if tag in (7, 9, 10, 11, 8, 12, 16, 19, 20):
                e = e[1:]
                self.cp[i].clear()
                try:
                    self.cp[i] += [tag] + [self.cp[x - 1] for x in e]
                except TypeError:
                    print(tag, e, self.cp)
                    raise

            elif tag in (15, 17, 18):
                self.cp[i] = self.cp[i][:2] + [self.cp[self.cp[i][-1] - 1]]

        self.cp = [makeStatic(e) for e in self.cp]

        # As by https://docs.oracle.com/javase/specs/jvms/se16/html/jvms-4.html#jvms-4.1-200-E.1
        self.access |= pop_u2(data)
        self.is_public = bool(self.access & 0x0001)
        self.is_final = bool(self.access & 0x0010)
        self.is_special_super = bool(self.access & 0x0020)
        self.is_interface = bool(self.access & 0x0200)
        self.is_abstract = bool(self.access & 0x0400)
        self.is_synthetic = bool(self.access & 0x1000)
        self.is_annotation = bool(self.access & 0x2000)
        self.is_enum = bool(self.access & 0x4000)
        self.is_module = bool(self.access & 0x8000)

        self.name: str = self.cp[pop_u2(data) - 1][1][1]
        self.parent: typing.Callable[
            [], typing.Coroutine[typing.Optional[AbstractJavaClass]]
        ] = await self.vm.get_lazy_class(
            self.cp[pop_u2(data) - 1][1][1], version=self.internal_version
        )

        self.interfaces += [
            await self.vm.get_lazy_class(
                self.cp[pop_u2(data) - 1][1][1], version=self.internal_version
            )
            for _ in range(pop_u2(data))
        ]

        for _ in range(pop_u2(data)):
            field = JavaField()
            await field.from_data(self, data)

            if field.access & 0x4000:
                self.enum_fields.append(field.name)

            self.fields[field.name] = field

            if field.access & 0x0008:
                self.static_field_values[field.name] = None
            else:
                self.dynamic_field_keys.add(field.name)

        for _ in range(pop_u2(data)):
            method = JavaMethod()
            await method.from_data(self, data)

            self.methods[(method.name, method.signature)] = method

        await self.attributes.from_data(self, data)

    async def get_method(self, name: str, signature: str, inner=False) -> JavaMethod:
        des = (name, signature)
        if des in self.methods:
            return self.methods[des]

        if self.parent is not None:
            parent = await self.parent()
            if isinstance(parent, typing.Awaitable):
                parent = await parent

        try:
            m = (await parent.get_method(*des)) if self.parent is not None else None
        except StackCollectingException as e:
            for interface in self.interfaces:
                try:
                    m = await (await interface()).get_method(*des)
                except StackCollectingException:
                    pass
                else:
                    break
            else:
                e.add_trace(f"not found up in {self.name}")
                raise

        if m is not None:
            return m

        raise StackCollectingException(
            f"class {self.name} has not method {name} with signature {signature}"
        )

    async def get_static_attribute(self, name: str, expected_type=None):
        if name not in self.static_field_values:
            if self.parent is not None:
                parent = await self.parent()
                if isinstance(parent, typing.Awaitable):
                    parent = await parent

                try:
                    return await parent.get_static_attribute(name)
                except KeyError:
                    pass

            # interfaces do not provide fields, don't they?

        try:
            return self.static_field_values[name]
        except KeyError:
            raise StackCollectingException(
                f"class {self.name} has no attribute '{name}' (class instance: {self})"
            ) from None

    def set_static_attribute(self, name: str, value, descriptor=None):
        self.static_field_values[name] = value

    async def bake(self):
        """
        Helper method for setting up a class
        Does some fancy work on annotations
        """

        for method in self.on_bake:
            method(self)

        self.on_bake.clear()

        if "RuntimeVisibleAnnotations" in self.attributes.attributes:
            await self.process_annotation(self.attributes["RuntimeVisibleAnnotations"])

        if "RuntimeInvisibleAnnotations" in self.attributes.attributes:
            await self.process_annotation(self.attributes["RuntimeInvisibleAnnotations"])

        for method in self.methods.values():
            attribute: JavaAttributeTable = method.attributes

            if "RuntimeVisibleAnnotations" in attribute.attributes:
                await self.process_annotation(attribute.attributes["RuntimeVisibleAnnotations"], target=method)

            if "RuntimeInvisibleAnnotations" in attribute.attributes:
                await self.process_annotation(attribute.attributes["RuntimeInvisibleAnnotations"], target=method)

    async def process_annotation(self, data, target=None):
        if target is None: target = self

        for annotation in data:
            for cls_name, args in annotation.annotations:
                try:
                    cls = await self.vm.get_class(cls_name, version=self.internal_version)
                except StackCollectingException as e:
                    # checks if the class exists, this will be true if it is a here class loader exception
                    if (
                        e.text.startswith("class ")
                        and e.text.endswith(" not found!")
                        and len(e.traces) == 0
                    ):
                        # todo: can we do something else here, maybe add a flag to get_class to return None if the class
                        #   could not be loaded -> None check here
                        print("classloading exception for annotation ignored")
                        traceback.print_exc()
                        print(e.format_exception())
                    else:
                        e.add_trace(
                            f"runtime annotation handling @class {self.name} loading class {cls_name}"
                        )
                        raise
                else:
                    await cls.on_annotate(target, args)

    async def create_instance(self):
        # Abstract classes cannot have instances
        if self.is_abstract:
            raise StackCollectingException(
                f"class {self.name} is abstract, so we cannot create an instance of it!"
            )

        obj = JavaClassInstance(self)
        await obj.init_fields()
        return obj

    def __repr__(self):
        return f"JavaBytecodeClass@{hex(id(self))[2:]}({self.name},access={bin(self.access)},parent=...,interfaces=...)"

    async def get_dynamic_field_keys(self):
        parent = await self.parent()
        if isinstance(parent, typing.Awaitable):
            parent = await parent

        return self.dynamic_field_keys | await parent.get_dynamic_field_keys()

    async def is_subclass_of(self, class_name: str):
        return (
            self.name == class_name
            or (await self.parent()).is_subclass_of(class_name)
            or any(
                interface().is_subclass_of(class_name) for interface in self.interfaces
            )
        )

    async def prepare_use(self, runtime=None):
        """
        Method for late-init-ing some stuff
        Can be called more than one time, only the first time will do stuff
        :param runtime: optional, the runtime instance to use during invoking the class init method when arrival

        todo: maybe load the function bytecode also here?
        """

        if self.class_init_complete:
            return

        self.class_init_complete = True

        if ("<clinit>", "()V") in self.methods:
            if runtime is None:
                try:
                    import jvm.Runtime
                except ImportError:
                    # If we have no way to invoke bytecode, don't do so
                    return

                runtime = jvm.Runtime.Runtime()

            try:
                await runtime.run_method(await self.get_method("<clinit>", "()V", inner=True))
            except StackCollectingException as e:
                e.add_trace(f"during class init of {self.name}")
                raise

    def validate_class_file(self):
        """
        Validation script on the overall class file

        Method validation happens during each method optimisation, starting at first method invocation,
            or some script interacting with it.
        """

        # validates the access flags
        if self.is_module:
            return

        if self.is_interface:
            if not self.is_abstract:
                raise RuntimeError(f"class {self.name} is interface, but not abstract")

            if self.is_final:
                raise RuntimeError(
                    f"class {self.name} is interface and final, which is not allowed"
                )

            if self.is_special_super:
                raise RuntimeError(
                    f"class {self.name} is interface and special-super-handling, which is not allowed"
                )

            if self.is_enum:
                raise RuntimeError(
                    f"class {self.name} is interface and an enum, which is not allowed"
                )

        else:
            if self.is_abstract and self.is_final:
                raise RuntimeError(
                    f"class {self.name} is abstract and final, which is not allowed"
                )

    def inject_method(self, name: str, signature: str, method, force=True):
        if not force and (name, signature) in self.methods:
            return

        self.methods[(name, signature)] = method

    async def dump(self) -> bytearray:
        """
        This method does the opposite to most of the stuff here
        It dumps the content of the class into a .class file
        """

        data = bytearray()
        data += U4.pack(0xCAFEBABE)

        major, minor = self.class_file_version
        data += U2.pack(minor)
        data += U2.pack(major)

        end_data = bytearray()

        # todo: parse access flags from attributes
        end_data += U2.pack(self.access)
        end_data += U2.pack(self.ensure_data([7, [1, self.name]]))
        end_data += U2.pack(self.ensure_data([7, [1, (await self.parent()).name if self.parent is not None else "java/lang/Object"]]))

        end_data += U2.pack(len(self.interfaces))
        end_data += b"".join([U2.pack(self.ensure_data([7, [1, e().name]])) for e in self.interfaces])

        end_data += U2.pack(len(self.fields))
        end_data += b"".join([field.dump() for field in self.fields.values()])

        end_data += U2.pack(len(self.methods))
        end_data += b"".join([method.dump() for method in self.methods.values()])

        # here encode the rest of the class body

        cp_data = bytearray()

        i = 0
        while i < len(self.cp):
            entry = self.cp[i]
            if entry is None: continue

            tag, *d = entry

            match tag:
                case 1:
                    s = entry[1].encode("utf-8")
                    cp_data += b"\x01" + U2.pack(len(s)) + s
                case 3:
                    cp_data += b"\x03" + INT.pack(entry[1])
                case 4:
                    cp_data += b"\x04" + FLOAT.pack(entry[1])
                case 5:
                    cp_data += b"\x05" + LONG.pack(entry[1])
                case 6:
                    cp_data += b"\x06" + DOUBLE.pack(entry[1])
                case 7:  # class
                    cp_data += b"\x07" + U2.pack(self.ensure_data(entry[1]))
                case 8:
                    cp_data += b"\x08" + U2.pack(self.ensure_data(entry[1]))
                case 9:
                    cp_data += b"\x09" + U2.pack(self.ensure_data(entry[1])) + U2.pack(self.ensure_data(entry[2]))
                case 10:
                    cp_data += b"\x0A" + U2.pack(self.ensure_data(entry[1])) + U2.pack(self.ensure_data(entry[2]))
                case 11:
                    cp_data += b"\x0B" + U2.pack(self.ensure_data(entry[1])) + U2.pack(self.ensure_data(entry[2]))
                case 12:
                    cp_data += b"\x0C" + U2.pack(self.ensure_data(entry[1])) + U2.pack(self.ensure_data(entry[2]))
                case _:
                    raise RuntimeError(tag, entry)

        data += U2.pack(len(self.cp) + 1)
        data += cp_data

        data += end_data

        return data

    def ensure_data(self, data: typing.List) -> int:
        if data not in self.cp:
            index = len(self.cp) + 1
            self.cp.append(data)
            if data[0] in (5, 6):
                self.cp.append(None)
            return index
        return self.cp.index(data) + 1


class JavaClassInstance(AbstractJavaClassInstance):
    """
    An instance of a java bytecode class
    Wires down some stuff to the underlying class and holds the dynamic field values

    todo: add abstract base so natives can share the same layout
    todo: add set/get for fields & do type validation
    """
    # __slots__ = AbstractJavaClassInstance.__slots__ + ("class_file", "fields")

    def __init__(self, class_file: JavaBytecodeClass):
        super().__init__()

        self.class_file = class_file

    async def init_fields(self):
        self.fields.update({name: None for name in await self.class_file.get_dynamic_field_keys()})

    async def get_method(self, name: str, signature: str):
        return await self.class_file.get_method(name, signature)

    def __repr__(self):
        return f"JavaByteCodeClassInstance@{hex(id(self))[2:]}(of={self.class_file},fields={self.fields})"

    def get_real_class(self):
        return self.class_file

    def get_field(self, name: str):
        return self.fields[name]

    def set_field(self, name: str, value):
        self.fields[name] = value


