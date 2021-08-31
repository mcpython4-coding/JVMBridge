"""
How are natives defined?

Natives are listed in "index" files defining which classes exists and what they provide.

Annotation handle types:
- "skip": don't core
- "track": mark the annotated object with the given annotation
- "report": report it to an event handler

Structure:
    - version attribute: some attribute passed to all classes handled by this, default to global space
    - annotations:
        <annotation handle type> -> affected class list
    - classes:
        <class name> ->
            - super[: which class this extends from
            - class type: the class type, defaults to a normal class, arrival are also "enum", "interface" and "abstract"
            - wraps: some python class this is wrapping, first module, than after a ":" the path in the module,
                builtin python's start with a ':'
            - hard wrap: if the object hard wraps that object, meaning we need a instance of it for work
            - mapping: A list of other names of this class
            - annotation: some annotation type this class provide, see above for possible values
            - attributes: <attr name> ->
                - access: some access modifier
                - expected type: some expected type
                - mapping: a list of other names of this attribute
                - default value: a value to insert, eval()-ed
            - methods: "<method name><method signature>" ->
                - access
                - mapping: a list of other names of this method
                - no effect: set if the method body should be empty, so nothing should happen on invocation
                - default result: if no effect is set, this can be a custom non-null value returned
                - wraps: optionally, a format-able string with aN as arg placeholders

    - implementation:
        Module & directory list
"""
import importlib
import json
import os
import traceback
import typing

import jvm.api
from jvm.api import AbstractJavaClass
from .JavaExceptionStack import StackCollectingException

from .native_building import addClassAttribute, addMethod

try:
    from mcpython import shared
except ImportError:
    shared = None


class NoMethod(jvm.api.AbstractMethod):
    def __init__(self, class_file, name: str, signature: str):
        super().__init__()
        self.class_file = class_file
        self.name = name
        self.signature = signature

        self.warned = False

    def invoke(self, args):

        if not self.warned:
            print(f"[BUILTIN][WARN] method {self} was invoked without implementation")
            self.warned = True

    def get_class(self):
        return self.class_file

    def __repr__(self):
        return f"UndefinedBuiltinMethod({self.class_file.name}:{self.name}{self.signature})"


class WrappedMethod(jvm.api.AbstractMethod):
    def __init__(self, class_file, name: str, signature: str, wrapped: typing.Callable):
        super().__init__()
        self.class_file = class_file
        self.name = name
        self.signature = signature
        self.wrapped = wrapped

    def invoke(self, args):
        result = self.wrapped(*args)
        if self.signature[-1] == "Z":
            result = int(result) if isinstance(result, bool) else 0
        return result

    def get_class(self):
        return self.class_file

    def __repr__(self):
        return f"ImplementedBuiltinMethod({self.class_file.name}:{self.name}{self.signature}@{self.wrapped})"


class NativeClass(jvm.api.AbstractJavaClass):
    def __init__(self):
        super().__init__()

        self.super_class = []
        self.method_table = {}
        self.static_attributes = {}

        self.dynamic_attribute_keys = set()

        self.attribute_mapping = {}
        self.method_mapping = {}

        self.report_annotations = -1

        self.enum_obj_counter = 0

        self.vm = jvm.api.vm

    def __repr__(self):
        return f"NativeClass({self.name}@{hex(id(self))[2:]})"

    def get_method(self, name: str, signature: str, inner=False):
        identifier = name + signature

        if identifier in self.method_mapping:
            identifier = self.method_mapping[identifier]
            name, signature = identifier.split("(")
            signature = "(" + signature

        if identifier not in self.method_table:
            addMethod(self.name, self.internal_version, identifier)

        return self.method_table.setdefault(identifier, NoMethod(self, name, signature))

    def map_attribute_name(self, name: str):
        return name if name not in self.attribute_mapping else self.attribute_mapping[name]

    def get_static_attribute(self, name: str, expected_type=None):
        name = self.map_attribute_name(name)

        if name not in self.static_attributes:
            print(f"[NATIVE] class {self.name} is missing attribute {name}")

            addClassAttribute(self.name, self.internal_version, name)

            return self.static_attributes.setdefault(name, None)

        return self.static_attributes[name]

    def set_static_attribute(self, name: str, value):
        name = self.map_attribute_name(name)

        if name not in self.static_attributes:
            print(f"[NATIVE] class {self.name} is missing attribute {name}")

            addClassAttribute(self.name, self.internal_version, name)

        self.static_attributes[name] = value

    def create_instance(self):
        return NativeClassInstance(self)

    def inject_method(self, name: str, signature: str, method, force=True):
        self.method_table[name+signature] = method

    def is_subclass_of(self, class_name: str) -> bool:
        return class_name == self.name or any(cls.is_subclass_of(class_name) for cls in self.super_class)

    def on_annotate(self, obj, args):
        if self.report_annotations == -1:
            print(f"{self} cannot be used as an annotation with args {args} on {obj}")
            return

        if callable(self.report_annotations):
            self.report_annotations(self, obj, args)

    def set_method(self, signature: str, method: jvm.api.AbstractMethod, force=False):
        if force or signature not in self.method_table:
            self.method_table[signature] = method

    def __repr__(self):
        return f"NativeClass(name={self.name},bound_version={self.internal_version})"


class PyObjWrappingClass(NativeClass):
    def __init__(self, wrapped_type: typing.Type):
        super().__init__()
        self.wrapped_type = wrapped_type

    def create_instance(self):
        return self.wrapped_type()


class NativeClassInstance(jvm.api.AbstractJavaClassInstance):
    def __init__(self, cls: NativeClass):
        super().__init__()

        self.cls = cls

        self.fields = {e: None for e in cls.dynamic_attribute_keys}

    def get_field(self, name: str):
        name = self.cls.map_attribute_name(name)

        return self.fields[name]

    def set_field(self, name: str, value):
        name = self.cls.map_attribute_name(name)

        if name not in self.fields: raise KeyError(name)

        self.fields[name] = value

    def get_method(self, name: str, signature: str):
        return self.cls.get_method(name, signature)

    def get_class(self) -> AbstractJavaClass:
        return self.cls

    def __repr__(self):
        return f"NativeClassInstance@{hex(id(self))[2:]}(of={self.cls})"


class PyObjWrappingClassInstance(jvm.api.AbstractJavaClassInstance):
    def __init__(self, cls: PyObjWrappingClass, underlying):
        super().__init__()

        self.cls = cls
        self.underlying = underlying

    def get_field(self, name: str):
        name = self.cls.map_attribute_name(name)

        return self.fields[name] if name in self.fields else getattr(self.underlying, name)

    def set_field(self, name: str, value):
        name = self.cls.map_attribute_name(name)

        if hasattr(self.underlying, name):
            setattr(self.underlying, name, value)
        else:
            self.fields[name] = value

    def get_method(self, name: str, signature: str):
        return self.cls.get_method(name, signature)

    def get_class(self) -> AbstractJavaClass:
        return self.cls


class BuiltinHandler:
    def __init__(self):
        self.classes: typing.Dict[typing.Any, typing.Dict[str, NativeClass]] = {}
        self.class_creation_binds = {}

    def create_class(self, name: str, version=None, class_type=NativeClass, class_creation_args=tuple()) -> NativeClass:
        if name in self.classes.setdefault(version, {}): return self.classes[version][name]
        if name in self.classes.setdefault(None, {}): return self.classes[None][name]

        cls = class_type(*class_creation_args)
        cls.name = name
        cls.internal_version = version

        self.classes[version][name] = cls

        jvm.api.vm.register_direct(cls)

        return cls

    def bind_method(self, cls: str, name: str = None, signature: str = None, version=None):
        if name is None:
            cls, e = cls.split(":")
            name = e.split("(")[0]
            signature = "("+e.split("(")[1]

        cls = self.create_class(cls, version)

        def bind(function):
            bound = WrappedMethod(cls, name, signature, function)

            cls.set_method(name+signature, bound, True)

            return function

        return bind

    def bind_class_creation(self, cls: str, version=None) -> typing.Callable[[typing.Callable[[NativeClass], None]], typing.Callable[[NativeClass], None]]:
        def bind(function: typing.Callable[[NativeClass], None]):
            self.class_creation_binds.setdefault((cls, version), []).append(function)
            return function

        return bind

    def bind_class_annotation(self, name: str, version=None) -> typing.Callable[[typing.Callable], typing.Callable]:
        def bind(function: typing.Callable[[NativeClass], None]):
            cls = self.create_class(name, version)
            cls.report_annotations = function
            return function

        return bind


handler = BuiltinHandler()


def parseAnnotationType(cls: NativeClass, t):
    if cls.report_annotations != -1: return

    if t == "skip":
        cls.report_annotations = 1
    elif t == "track":
        cls.report_annotations = 1
    else:
        cls.report_annotations = 2


def parse_wrap(text: str):
    if text.startswith(":"):
        import builtins
        return getattr(builtins, text[1:])
    else:
        module = importlib.import_module(text.split(":")[0])
        parts = text.split(":")[1].split(".")
        for e in parts:
            module = getattr(module, e)
        return module


def create_method_based_on_wrap(cls, name, signature, code):
    def execute(*args):
        local = {
            f"a{i}": e for i, e in enumerate(args)
        } | {"cls": cls, "shared": shared}
        try:
            return eval(code, globals(), local)
        except StackCollectingException as e:
            e.add_trace(code)
            raise
        except Exception as e:
            raise StackCollectingException(f"During invoking eval() for {cls.name}:{name}{signature}").add_trace(e).add_trace(code).add_trace(args) from None

    return WrappedMethod(cls, name, signature, execute)


def load_index_file(file: str):
    try:
        data: dict = json.load(open(file))
    except:
        raise RuntimeError(file)

    version = data.setdefault("version attribute", None)

    for name, d in data.setdefault("classes", {}).items():
        if "hard wrap" in d and d["hard wrap"]:
            cls = handler.create_class(name, version, class_type=PyObjWrappingClass, class_creation_args=(parse_wrap(d["wraps"]),))
        else:
            cls = handler.create_class(name, version)

        if "mapping" in d:
            for class_name in d["mapping"]:
                jvm.api.vm.register_special(cls, class_name)

        cls.super_class += d.setdefault("super", [])

        if "annotation" in d:
            parseAnnotationType(cls, d["annotation"])

        for attr_name, e in d.setdefault("attributes", {}).items():
            if "static" in e.setdefault("access", ""):
                if "enum" in e["access"]:
                    cls.static_attributes[attr_name] = f"{cls.name}::EnumElement<{cls.enum_obj_counter}>::{attr_name}"
                    cls.enum_obj_counter += 1
                else:
                    if "default value" in e:
                        value = eval(e["default value"], globals())
                    else:
                        value = None

                    cls.static_attributes[attr_name] = value
            else:
                cls.dynamic_attribute_keys.add(attr_name)

            if "mapping" in e:
                for n in e["mapping"]:
                    cls.attribute_mapping[n] = attr_name

        for signature, e in d.setdefault("methods", {}).items():
            a, b = signature.split("(")

            if "wraps" in e:

                method = create_method_based_on_wrap(cls, a, "("+b, e["wraps"])

            elif e.setdefault("no effect", False):
                result = e.setdefault("default result", None)
                method = WrappedMethod(cls, a, "("+b, lambda *_: result)
            else:
                method = NoMethod(cls, a, "("+b)

            access = e.setdefault("access", "")

            if "static" in access:
                method.access |= 0x0008

            if "abstract" in access:
                method.access |= 0x0400

            cls.set_method(signature, method)

            if "mapping" in e:
                for n in e["mapping"]:
                    cls.method_mapping[(n+"("+signature.split("(")[1:])] = signature

        if (name, version) in handler.class_creation_binds:
            for method in handler.class_creation_binds.pop((name, version)):
                method(cls)

    for t, d in data.setdefault("annotations", {}).items():
        for cls in d:
            cls = handler.create_class(cls, version)
            parseAnnotationType(cls, t)

    local = os.path.dirname(__file__)+"/binding"

    for file in data.setdefault("implementation", []):
        if file.endswith("/"):
            for root, _, files in os.walk(local+"/"+file[:-1]):
                for f in files:
                    with open(os.path.join(root, f)) as fa:
                        data = fa.read()

                    try:
                        exec(data)
                    except:
                        print(f"in file: {f}")
                        traceback.print_exc()
        else:
            importlib.import_module("jvm.binding."+file.replace("/", "."))


def load_implementations():
    pass


def load_default_indexes():
    local = os.path.dirname(__file__)+"/binding"

    for file in os.listdir(local):
        if file.endswith(".json"):
            load_index_file(local+"/"+file)

    load_implementations()
