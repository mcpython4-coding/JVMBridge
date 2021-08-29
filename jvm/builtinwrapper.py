import typing
from abc import ABC

from jvm.api import AbstractJavaClass
from jvm.api import AbstractJavaClassInstance
from jvm.api import DYNAMIC_NATIVES
import jvm.api
from jvm.JavaExceptionStack import StackCollectingException


class NativeClass(AbstractJavaClass, ABC):
    NAME = None
    EXPOSED_VERSIONS: typing.Optional[set] = None

    ALLOW_FUNCTION_ADDITION = True

    @classmethod
    def __init_subclass__(cls, **kwargs):
        if cls.NAME is not None:

            if cls.EXPOSED_VERSIONS is None:
                jvm.api.vm.register_native(cls)
            else:
                # todo: add flag to share native
                for version in cls.EXPOSED_VERSIONS:
                    jvm.api.vm.register_native(cls, version)

    def __init__(self):
        super().__init__()
        self.vm = jvm.api.vm
        self.name = self.NAME

        self.exposed_attributes = {}
        self.exposed_methods = {}
        self.parent = self.__class__.__bases__[0]
        self.injected_methods = []

        self.children: typing.List[AbstractJavaClass] = []

        for key, value in self.__class__.__dict__.items():
            if hasattr(value, "native_name"):
                method = getattr(self, key)

                if not callable(method):
                    raise StackCollectingException(
                        f"in native: {self.name}: assigned method {value.native_name} cannot be assigned to native as something dynamic overides it later"
                    )

                self.exposed_methods.setdefault(
                    (value.native_name, value.native_signature), method
                )

        if not isinstance(self.parent, NativeClass):
            self.parent = None
        else:
            self.parent.children.append(self)

            for injected in self.parent.injected_methods:
                self.inject_method(*injected, force=False)

    def inject_method(self, name: str, signature: str, method, force=True):
        if force or (name, signature) in self.exposed_methods:
            self.exposed_methods[(name, signature)] = method

        for child in self.children:
            child.inject_method(name, signature, method, force=False)

        self.injected_methods.append((name, signature, method))

    def get_method(self, name: str, signature: str, inner=False):
        try:
            return self.exposed_methods[(name, signature)]
        except KeyError:
            try:
                m = (
                    self.parent.get_method(name, signature, inner=True)
                    if self.parent is not None
                    else None
                )

                if m is None:
                    for interface in self.interfaces:
                        m = interface.get_method(name, signature, inner=True)
                        if m is not None:
                            return m

                else:
                    return m

            except StackCollectingException as e:
                e.add_trace(f"not found up at {self.name}")
                raise

        if DYNAMIC_NATIVES and self.ALLOW_FUNCTION_ADDITION:

            @native(name, signature)
            def dynamic(*_):
                pass

            self.exposed_methods[(name, signature)] = dynamic

            print(
                f"""
Native Dynamic Builder: Class {self.name}
Method {name} with signature {signature}
Add:
    @native(\"{name}\", \"{signature}\")
    def {name.removeprefix("<").removesuffix(">").replace("$", "__")}(self, *_):
        pass"""
            )

            return dynamic

        raise StackCollectingException(
            f"class {self.name} has no method named '{name}' with signature {signature}"
        ).add_trace(str(self)).add_trace(
            str(list(self.exposed_methods.keys()))
        ) from None

    def get_static_attribute(self, name: str, expected_type=None):
        if name not in self.exposed_attributes:
            if DYNAMIC_NATIVES:
                print(
                    f"""
Native Dynamic Builder: Class {self.name}
Static attribute {name}"""
                )
                self.exposed_attributes[name] = None
                return

            raise StackCollectingException(
                f"unknown static attribute '{name}' of class '{self.name}' (expected type: {expected_type})"
            )

        return self.exposed_attributes[name]

    def set_static_attribute(self, name: str, value):
        self.exposed_attributes[name] = value

    def create_instance(self):
        return NativeClassInstance(self)

    def __repr__(self):
        return f"NativeClass({self.NAME})"

    def is_subclass_of(self, class_name: str):
        return self.name == class_name

    def iter_over_instance(self, instance) -> typing.Iterable:
        raise StackCollectingException(f"unable to iterate over {instance}")

    def get_custom_info(self, instance) -> str:
        return ""


class NativeClassInstance(AbstractJavaClassInstance):
    def __init__(self, native_class: "NativeClass"):
        self.native_class = native_class
        self.fields = {key: None for key in native_class.get_dynamic_field_keys()}

    def get_field(self, name: str):
        return self.fields[name]

    def set_field(self, name: str, value):
        self.fields[name] = value

    def get_method(self, name: str, signature: str):
        return self.native_class.get_method(name, signature)

    def get_class(self):
        return self.native_class

    def __repr__(self):
        c = self.native_class.get_custom_info(self)
        return f"NativeClassInstance(of={self.native_class},id={hex(id(self))}"+(",custom="+c if c is not None else c)+")"

    def __hash__(self):
        return id(self) if not hasattr(self.native_class, "get_hash") else self.native_class.get_hash(self)


def native(name: str, signature: str, static=False):
    def setup(m):

        if signature[-1] == "Z":
            # todo: do this with bytecode manipulation
            def method(*args):
                r = m(*args)
                r = int(r) if r is not None else 0
                return r
        else:
            method = m

        method.native_name = name
        method.native_signature = signature
        method.access = 0x1101 | (
            0 if not static else 0x0008
        )  # public native synthetic (static)
        return method

    return setup