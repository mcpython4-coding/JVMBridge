import typing
import weakref
from abc import ABC

from jvm.util import decode_cp_constant
from jvm.util import pop_sized
from jvm.util import pop_u1
from jvm.util import pop_u2
from jvm.util import pop_u4
from jvm.util import U2
from jvm.util import U4
from jvm.JavaExceptionStack import StackCollectingException
import jvm.api
from jvm.api import AbstractJavaClass


class AbstractAttributeParser(ABC):
    NAME: str = None

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        raise NotImplementedError

    def dump(self, table: "JavaAttributeTable") -> bytearray:
        raise NotImplementedError


class ConstantValueParser(AbstractAttributeParser):
    __slots__ = (
        "value",
        "field",
        "data",
    )

    def __init__(self):
        self.value = None
        self.field: "JavaField" = None
        self.data = None

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        self.value = table.class_file.cp[pop_u2(data)]
        self.field = table.parent

        if self.field.access & 0x0008:
            table.class_file.on_bake.append(self.inject_static)
        # else:
        #     table.class_file.on_instance_creation.append(self.inject_instance)

    def inject_static(self, class_file: "JavaBytecodeClass"):
        class_file.set_static_attribute(self.field.name, self.value)

    def inject_instance(self, class_file: "JavaBytecodeClass", instance):
        instance.set_attribute(self.field.name, self.value)

    def dump(self, table: "JavaAttributeTable") -> bytes:
        return U2.pack(table.class_file.ensure_data)


class CodeParser(AbstractAttributeParser):
    __slots__ = (
        "class_file",
        "table",
        "max_stacks",
        "max_locals",
        "code",
        "exception_table",
        "attributes",
    )

    def __init__(self):
        self.class_file: "JavaBytecodeClass" = None
        self.table: "JavaAttributeTable" = None
        self.max_stacks = 0
        self.max_locals = 0
        self.code: bytes = None
        self.exception_table = {}
        self.attributes = JavaAttributeTable(self)

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        self.table = table
        self.class_file = table.class_file
        self.max_stacks = pop_u2(data)
        self.max_locals = pop_u2(data)
        size = pop_u4(data)
        self.code = pop_sized(size, data)

        for _ in range(pop_u2(data)):
            start, end, handler, catch = (
                pop_u2(data),
                pop_u2(data),
                pop_u2(data),
                pop_u2(data),
            )
            self.exception_table.setdefault(start, []).append((end, handler, catch))

        await self.attributes.from_data(table.class_file, data)

    def dump(self, table: "JavaAttributeTable") -> bytearray:
        data = bytearray()
        data += U2.pack(self.max_locals)
        data += U2.pack(self.max_stacks)

        data += U4.pack(len(self.code))
        data += self.code

        data += U2.pack(len(self.exception_table))
        for start, (end, handler, catch) in self.exception_table.items():
            data += U2.pack(start) + U2.pack(end) + U2.pack(handler) + U2.pack(catch)

        data += self.attributes.dump()
        return data


class BootstrapMethods(AbstractAttributeParser):
    __slots__ = ("entries",)

    def __init__(self):
        self.entries = []

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        for _ in range(pop_u2(data)):
            method_ref = table.class_file.cp[pop_u2(data) - 1]
            arguments = [
                table.class_file.cp[pop_u2(data) - 1] for _ in range(pop_u2(data))
            ]
            self.entries.append((method_ref, arguments))

    def dump(self, table: "JavaAttributeTable") -> bytearray:
        data = bytearray()
        for method, args in self.entries:
            data += table.class_file.ensure_data(method)
            data += U2.pack(len(args)) + b"".join([
                U2.pack(table.class_file.ensure_data(arg)) for arg in args
            ])
        return data


class StackMapTableParser(AbstractAttributeParser):
    __slots__ = ("entries",)

    @classmethod
    def parse_verification_type_info(cls, data: bytearray):
        tag = pop_u1(data)
        # print(2, tag)

        match tag:
            case 0:  # TOP
                return 0,
            case 1:  # Integer
                return "I",
            case 2:  # Float
                return "F",
            case 3:  # Long
                return "J",
            case 4:  # Double
                return "D",
            case 5:  # null
                return None,
            case 6:  # UninitializedThis
                return 4,
            case 7:  # Object_variable
                return 7, pop_u2(data)
            case 8:  # Uninitialized_variable
                return 8, pop_u2(data)

        # raise ValueError(tag)

    def __init__(self):
        self.entries = []

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        for _ in range(pop_u2(data)):
            entry_type = pop_u1(data)
            # print(1, entry_type)

            # same_frame
            if entry_type < 64:
                self.entries.append((entry_type, entry_type))

            # same_locals_1_stack_item_frame
            elif entry_type < 128:
                self.entries.append((entry_type, entry_type - 64, self.parse_verification_type_info(data)))

            elif entry_type < 247:
                continue
                # raise StackCollectingException("Reserved tag for StackMapTable: "+str(entry_type)).add_trace(table.class_file.name)

            # same_locals_1_stack_item_frame_extended
            elif entry_type == 247:
                self.entries.append((entry_type, pop_u2(data), self.parse_verification_type_info(data)))

            # chop_frame
            elif entry_type < 251:
                self.entries.append((entry_type, pop_u2(data), 251 - entry_type))

            # same_frame_extended
            elif entry_type == 251:
                self.entries.append((entry_type, pop_u2(data)))

            # append_frame
            elif entry_type < 255:
                self.entries.append((entry_type, pop_u2(data), self.parse_verification_type_info(data)))

            # full_frame
            elif entry_type == 255:
                self.entries.append((entry_type, pop_u2(data), [self.parse_verification_type_info(data) for _ in range(pop_u2(data))], [self.parse_verification_type_info(data) for _ in range(pop_u2(data))]))

    def dump(self, table: "JavaAttributeTable") -> bytearray:
        return bytearray()  # todo: implement


class ElementValue:
    __slots__ = (
        "tag",
        "data",
        "raw_data",
    )

    def __init__(self):
        self.tag = None
        self.data = None
        self.raw_data = None

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        # as by https://docs.oracle.com/javase/specs/jvms/se16/html/jvms-4.html#jvms-4.7.16

        self.tag = tag = chr(pop_u1(data))

        # these can be directly loaded from the constant pool
        if tag in "BCDFIJSZs":
            self.data = await decode_cp_constant(table.class_file.cp[pop_u2(data) - 1], vm=table.class_file.vm)

        elif tag == "e":
            cls_name = (
                table.class_file.cp[pop_u2(data) - 1][1]
                .removeprefix("L")
                .removesuffix(";")
            )
            attr_name = table.class_file.cp[pop_u2(data) - 1][1]
            self.raw_data = cls_name, attr_name

            cls = await table.class_file.vm.get_class(cls_name, version=table.class_file.internal_version)

            if cls is not None:
                self.data = await cls.get_static_attribute(attr_name, "enum")

        elif tag == "c":
            self.data = table.class_file.cp[pop_u2(data) - 1]

        elif tag == "[":
            self.data = [await ElementValue().parse(table, data) for _ in range(pop_u2(data))]

        elif tag == "@":
            annotation_type = (
                table.class_file.cp[pop_u2(data) - 1][1]
                .removeprefix("L")
                .removesuffix(";")
            )

            values = []

            for _ in range(pop_u2(data)):
                name = table.class_file.cp[pop_u2(data) - 1]
                if name[0] != 1:
                    raise StackCollectingException("invalid entry: "+str(name))

                name = name[1]
                value = await ElementValue().parse(table, data)
                values.append((name, value))

            self.data = annotation_type, values

        else:
            raise NotImplementedError(tag)

        return self

    def dump(self, table: "JavaAttributeTable") -> typing.Union[bytes, bytearray]:
        if self.tag in "BCDFIJSZs":
            return U2.pack(table.class_file.ensure_data(self.data))

        elif self.tag == "e":
            cls, attr = self.raw_data
            return U2.pack(table.class_file.ensure_data("L"+cls+";"))+U2.pack(table.class_file.ensure_data(attr))

        elif self.tag == "[":
            return U2.pack(len(self.data)) + sum([e.dump(table) for e in self.data])

        elif self.tag == "@":
            return U2.pack(table.class_file.ensure_data("L"+self.data[0]+";")) + U2.pack(len(self.data[1])) + b"".join([U2.pack(table.class_file.ensure_data([1, e]))+value.dump() for e, value in self.data[1]])

        raise NotImplementedError(self.tag)

    def __repr__(self):
        return f"ElementValue({self.data})"


class RuntimeAnnotationsParser(AbstractAttributeParser):
    __slots__ = ("annotations",)

    def __init__(self):
        self.annotations = []

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        for _ in range(pop_u2(data)):
            annotation_type = (
                table.class_file.cp[pop_u2(data) - 1][1]
                .removeprefix("L")
                .removesuffix(";")
            )

            values = []

            for _ in range(pop_u2(data)):
                name = table.class_file.cp[pop_u2(data) - 1]
                if name[0] != 1:
                    raise StackCollectingException(
                        f"invalid name @annotation head for ElementValue pair: {name}"
                    )

                name = name[1]

                try:
                    value = await ElementValue().parse(table, data)
                except StackCollectingException as e:
                    e.add_trace(
                        f"during decoding {self.__class__.__name__}-attribute for annotation class {annotation_type} annotating class {table.class_file.name}"
                    )
                    raise

                values.append((name, value))

            self.annotations.append((annotation_type, values))

        return self

    def dump(self, table: "JavaAttributeTable") -> bytearray:
        data = bytearray()
        data += U2.pack(len(self.annotations))

        for annotation_type, values in self.annotations:
            data += U2.pack(table.class_file.ensure_data([1, "L"+annotation_type+";"]))
            data += U2.pack(len(values))

            for name, v in values:
                data += U2.pack(table.class_file.ensure_data([1, name]))
                data += v.pack(table)

        return data


class NestHostParser(AbstractAttributeParser):
    __slots__ = ("host",)

    def __init__(self):
        self.host = None

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        self.host = table.class_file.cp[pop_u2(data) - 1][1][1]

    def dump(self, table: "JavaAttributeTable") -> bytearray:
        return table.class_file.ensure_data([7, [1, self.host]])


class NestMembersParser(AbstractAttributeParser):
    __slots__ = ("classes",)

    def __init__(self):
        self.classes = []

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        self.classes += [
            table.class_file.cp[pop_u2(data) - 1][1][1]
            for _ in range(pop_u2(data))
        ]

    def dump(self, table: "JavaAttributeTable") -> bytearray:
        return U2.pack(len(self.classes)) + sum(
            (
                table.class_file.ensure_data([7, [1, e]])
                for e in self.classes
            ),
            bytearray()
        )


class SignatureParser(AbstractAttributeParser):
    __slots__ = ("signature",)

    def __init__(self):
        self.signature = None

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        self.signature = table.class_file.cp[pop_u2(data) - 1][1]

    def dump(self, table: "JavaAttributeTable") -> bytearray:
        return table.class_file.ensure_data([1, self.signature])


class ExceptionsParser(AbstractAttributeParser):
    __slots__ = ("exceptions",)

    def __init__(self):
        self.exceptions = []

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        self.exceptions += [
            table.class_file.cp[pop_u2(data) - 1][1][1]
            for _ in range(pop_u2(data))
        ]

    def dump(self, table: "JavaAttributeTable") -> bytearray:
        return U2.pack(len(self.exceptions)) + sum(
            (
                table.class_file.ensure_data([7, [1, e]])
                for e in self.exceptions
            ),
            bytearray()
        )


class InnerClassesParser(AbstractAttributeParser):
    __slots__ = ("inner_classes",)

    def __init__(self):
        self.inner_classes = []

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        for _ in range(pop_u2(data)):
            inner_class_index = pop_u2(data)
            outer_class_index = pop_u2(data)
            inner_name_index = pop_u2(data)
            inner_class_access = pop_u2(data)
            self.inner_classes.append((inner_class_index, outer_class_index, inner_name_index, inner_class_access))

    def dump(self, table: "JavaAttributeTable") -> bytearray:
        return bytearray()  # todo: implement


class EnclosingMethodParser(AbstractAttributeParser):
    __slots__ = ("class_index", "method_index")

    def __init__(self):
        self.class_index, self.method_index = -1, -1

    async def parse(self, table: "JavaAttributeTable", data: bytearray):
        self.class_index, self.method_index = pop_u2(data), pop_u2(data)

    def dump(self, table: "JavaAttributeTable") -> bytearray:
        return U2.pack(self.class_index) + U2.pack(self.method_index)


class JavaAttributeTable:
    ATTRIBUTES_NEED_PARSING = {
        "ConstantValue",
        "Code",
        "StackMapTable",
        "BootstrapMethods",
        "NestHost",
        "NestMembers",
        "RuntimeVisibleAnnotations",
        "RuntimeInvisibleAnnotations",
    }
    ATTRIBUTES_MAY_PARSING = {
        "Exceptions",
        "InnerClasses",
        "EnclosingMethods",
        "Synthetic",
        "Signature",
        "Record",
        "SourceFile",
        "LineNumberTable",
        "LocalVariableTable",
        "LocalVariableTypeTable",
    }

    ATTRIBUTES = {
        "BootstrapMethods": BootstrapMethods,
        "Code": CodeParser,
        "ConstantValue": ConstantValueParser,
        "EnclosingMethod": EnclosingMethodParser,
        "Exceptions": ExceptionsParser,
        "InnerClasses": InnerClassesParser,
        "NestHost": NestHostParser,
        "NestMembers": NestMembersParser,
        "RuntimeInvisibleAnnotations": RuntimeAnnotationsParser,
        "RuntimeVisibleAnnotations": RuntimeAnnotationsParser,
        "Signature": SignatureParser,
        "StackMapTable": StackMapTableParser,
    }

    __slots__ = (
        "parent",
        "class_file",
        "attributes_unparsed",
        "attributes",
    )

    def __init__(self, parent):
        self.parent = parent
        self.class_file: AbstractJavaClass = None
        self.attributes_unparsed = {}
        self.attributes = {}

    async def from_data(self, class_file: AbstractJavaClass, data: bytearray):
        self.class_file = class_file

        for _ in range(pop_u2(data)):
            name = class_file.cp[pop_u2(data) - 1][1]
            data_size = pop_u4(data)
            d = pop_sized(data_size, data)
            self.attributes_unparsed.setdefault(name, []).append(d)

        for key in list(self.attributes_unparsed.keys()):
            if key in self.ATTRIBUTES:
                self.attributes.setdefault(key, [])

                for data in self.attributes_unparsed[key]:
                    instance = self.ATTRIBUTES[key]()
                    await instance.parse(self, bytearray(data))
                    self.attributes[key].append(instance)

                del self.attributes_unparsed[key]

        keyset = set(self.attributes_unparsed.keys())

        diff_need = self.ATTRIBUTES_NEED_PARSING.intersection(keyset)
        if diff_need:
            raise RuntimeError(
                f"The following attribute(s) could not be parsed (attribute holder: {self.parent}): "
                + ", ".join(diff_need)
            )

        diff_may = self.ATTRIBUTES_MAY_PARSING.intersection(keyset)
        # if diff_may:
        # info("missing attribute parsing for: " + ", ".join(diff_may))

    def __getitem__(self, item):
        return self.attributes[item]

    def dump(self) -> bytearray:
        data = bytearray()

        attributes = sum([(key, e) for e in data for key, data in self.attributes_unparsed.items()])
        attributes += sum([(key, e) for e in data for key, data in self.attributes.items()])

        data += U2.pack(len(attributes))

        for name, body in attributes:
            data += U2.pack(self.class_file.ensure_data([1, name]))

            body = body if not isinstance(body, AbstractAttributeParser) else body.dump(self)
            data += U4.pack(len(body))
            data += body

        return data