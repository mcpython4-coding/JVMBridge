import importlib
import json
import os.path
import re
import traceback
import typing

import simplejson

import jvm.api


class NativeMethod(jvm.api.AbstractMethod):
    """
    Wrapper implementation of a NativeMethod wrapping a python implemented
    method. See @bind_native() for binding a method to a native method
    """

    def __init__(self, cls: jvm.api.AbstractJavaClass, name: str, signature: str, underlying: typing.Callable, access: int = 1):
        super().__init__()
        self.cls = cls
        self.name = name
        self.signature = signature
        self.underlying = underlying
        self.access = access
        self.bound = False

    def invoke(self, args: typing.Iterable, stack=None):
        try:
            return self.underlying(self, stack, *args)
        except:
            print("during native", self, "with", args)
            raise

    def get_class(self):
        return self.cls
    
    def __repr__(self):
        return ("Bound" if self.bound else "Unbound")+f"NativeMethod({self.name}{self.signature}@{self.cls.name}::{self.access}"+("" if not self.bound else "->"+repr(self.underlying))+")"


class NativeClass(jvm.api.AbstractJavaClass):
    """
    A class in the JVM instance
    Bound from outside to the respective JVM instances
    Can be deserialized from a header file
    """

    def __init__(self, header: "NativeHeader", name: str):
        super().__init__()
        self.header = header
        self.name = name

        self.exposed_fields: typing.List[str] = []

        self.methods: typing.Dict[str, NativeMethod] = {}
        self.static_attributes: typing.Dict[str, typing.Any] = {}
        self.dynamic_attribute_keys: typing.Set[str] = set()

        self.parents: typing.Set[jvm.api.AbstractJavaClass] = set()

        self.enum_attribute_keys = set()

    def get_method(self, name: str, signature: str, inner=False, static=True):
        if name+signature not in self.methods:
            self.create_method(name, signature, 0x0008 if static else 0x0000)

        return self.methods[name+signature]

    def get_static_attribute(self, name: str, expected_type=None):
        if name not in self.static_attributes:
            self.create_attribute(name, expected_type, 0x0008)
        return self.static_attributes[name]

    def set_static_attribute(self, name: str, value, descriptor: str = None):
        if name not in self.static_attributes:
            self.create_attribute(name, descriptor, 0x0008)
        self.static_attributes[name] = value

    def create_instance(self) -> "NativeClassInstance":
        return NativeClassInstance(self)

    def inject_method(self, name: str, signature: str, method, force=True):
        if name+signature not in self.methods or force:
            self.methods[name+signature] = method

    def is_subclass_of(self, class_name: str) -> bool:
        return self.name == class_name and any(cls.is_subclass_of(class_name) for cls in self.parents)

    def parse_data(self, data: dict):
        if "attributes" in data:
            for name, d in data["attributes"].items():
                try:
                    if d["access"] & 0x0008:
                        self.static_attributes[name] = None
                    else:
                        self.dynamic_attribute_keys.add(name)

                    if "enum" in d["descriptor"] or d["access"] & 0x4000:
                        self.enum_attribute_keys.add(name)
                except:
                    print(name, d)
                    raise

        if "methods" in data:
            for desc, d in data["methods"].items():
                self.methods[desc] = NativeMethod(
                    self,
                    desc.split("(")[0],
                    "("+desc.split("(")[1],
                    lambda m, *_: print("error native does not exists", m),
                )

        if "exposed_attributes" in data:
            self.exposed_fields = data["exposed_attributes"]

    def create_attribute(self, name: str, descriptor: str, access: int):
        cls_data: dict = self.header.data[self.header.name2index[self.name]]
        cls_data.setdefault("attributes", {}).setdefault(name, {"descriptor": descriptor, "access": access})
        self.header.update_file()

        if access & 0x0008:
            self.static_attributes[name] = None

    def create_method(self, name: str, signature: str, access: int):
        cls_data: dict = self.header.data[self.header.name2index[self.name]]
        cls_data.setdefault("methods", {})[name+signature] = {"access": access}
        self.header.update_file()

        self.methods[name+signature] = NativeMethod(
            self,
            name,
            signature,
            lambda m, *_: print("error native does not exists", m)
        )

    def on_annotate(self, obj, args):
        self.get_method("onObjectAnnotation", "(Ljava/lang/Object;Ljava/lang/List;)V").invoke([obj, args])
        
    def __repr__(self):
        return f"NativeClass@{self.header.file.split('/')[-1].split('.')[0]}.h({self.name})"

    def get_dynamic_field_keys(self):
        return self.dynamic_attribute_keys


class NativeClassInstance(jvm.api.AbstractJavaClassInstance):
    def __init__(self, cls: NativeClass):
        super().__init__()
        self.cls = cls

        self.fields = {key: None for key in cls.dynamic_attribute_keys}

    def get_real_class(self) -> NativeClass:
        return self.cls

    def get_field(self, name: str):
        return self.fields[name]

    def set_field(self, name: str, value):
        if name not in self.fields:
            raise KeyError(name)
        self.fields[name] = value

    def get_method(self, name: str, signature: str):
        return self.cls.get_method(name, signature, static=False)
    
    def __repr__(self):
        exposed = [self.get_field(name) for name in self.cls.exposed_fields]
        return f"NativeClassInstance@{self.get_class().name}"+(f"@@{self.get_real_class().name}" if self.rebound_type else "")+"("+",".join(exposed)+")"


class NativeHeader:
    def __init__(self):
        self.data = []
        self.name2index = {}
        self.file = None

    def load_from_file(self, file: str):
        self.file = file
        with open(file) as f:
            self.data = json.load(f)

        self.parse_data()

    def parse_data(self):
        for i, cls_data in enumerate(self.data):
            try:
                cls = NativeClass(self, cls_data["name"])
                cls.parse_data(cls_data)
                jvm.api.vm.shared_classes[cls.name] = cls
                self.name2index[cls.name] = i
            except:
                print("during loading file", cls_data)
                raise

    def update_file(self):
        if self.file is None:
            raise RuntimeError
        with open(self.file, mode="w") as f:
            simplejson.dump(self.data, f, indent="  ")

    def create_class(self, name: str):
        self.data.append({"name": name})
        self.name2index[name] = len(self.data)-1
        self.update_file()
        return NativeClass(self, name)
    
    def __repr__(self):
        return ("Bound" if self.file is not None else "Unbound")+f"NativeHeader@{self.file}()"


class NativeManager:
    DEFAULT_HEADER_FILES = ["java", "forge", "mc", "ct_api", "netty", "jei", "google"]
    MATCHER2HEADER: typing.Dict[str, str] = {
        "java/": "java",
        "javax/": "java",
        "net/minecraftforge/": "forge",
        "mcp/": "forge",
        "net/minecraft/": "mc",
        "com/mojang/": "mc",
        "stanhebben/zenscript/": "ct_api",
        "crafttweaker/": "ct_api",
        "io/netty/": "netty",
        "mezz/jei/": "jei",
        "com/google/": "google",
    }

    def __init__(self):
        self.headers: typing.Dict[str, NativeHeader] = {}

    def load_files(self):
        root = os.path.dirname(__file__)+"/native/header/"
        for file in self.DEFAULT_HEADER_FILES:
            header = NativeHeader()
            header.load_from_file(root+file+".json")
            self.headers[file] = header

        root = os.path.dirname(__file__) + "/native/implementation/"
        for file in os.listdir(root):
            if not file.endswith(".py"): continue

            try:
                importlib.import_module("jvm.native.implementation."+file.split(".")[0].replace("/", "."))
            except ImportError as e:
                print(f"[JVM][WARN] failed to bind module {file.removesuffix('.py')}")
                traceback.print_exc()

    def get_header_for_cls(self, cls: str) -> typing.Optional[NativeHeader]:
        for matcher in self.MATCHER2HEADER.keys():
            if cls.startswith(matcher):
                return self.headers[self.MATCHER2HEADER[matcher]]


manager = NativeManager()


def bind_native(cls_name: str, action: str):
    cls: NativeClass = jvm.api.vm.shared_classes[cls_name]

    if not isinstance(cls, NativeClass):
        raise ValueError(cls_name)

    def bind(function):
        if action not in cls.methods:
            cls.create_method(action.split("(")[0], "("+action.split("(")[1], 0x0001)

        cls.methods[action].underlying = function
        cls.methods[action].bound = True
        return function

    return bind


def bind_annotation(cls_name: str):
    return bind_native(cls_name, "onObjectAnnotation(Ljava/lang/Object;Ljava/lang/List;)V")

