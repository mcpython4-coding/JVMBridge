import typing

import jvm.api
import jvm.Java
from jvm.api import AbstractJavaClass

REGISTERED_NATIVES = set()

COLLECTED_METHODS = []
COLLECTED_GETTERS = []
COLLECTED_SETTERS = []


class Native(AbstractJavaClass):
    NAME = None

    IS_ABSTRACT = False
    IS_INTERFACE = False

    METHODS = None

    SETTERS = None
    GETTERS = None

    DYNAMIC_FIELD_KEYS = dict()
    STATIC_FIELD_KEYS = dict()

    PARENTS = None

    PROTECT = False

    @classmethod
    def __init_subclass__(cls, **kwargs):
        if cls.PROTECT: return

        cls.METHODS = {}
        cls.SETTERS = {}
        cls.GETTERS = {}
        cls.PARENTS = []

        for parent in cls.__bases__:
            if issubclass(parent, Native) and parent != Native:
                cls.PARENTS.append(parent)
                cls.DYNAMIC_FIELD_KEYS |= parent.DYNAMIC_FIELD_KEYS
                cls.STATIC_FIELD_KEYS |= parent.STATIC_FIELD_KEYS

        for method in COLLECTED_METHODS:
            cls.METHODS[method.name, method.signature] = method
        COLLECTED_METHODS.clear()

        for attr, method in COLLECTED_GETTERS:
            cls.GETTERS[attr] = method
        COLLECTED_GETTERS.clear()

        for attr, method in COLLECTED_SETTERS:
            cls.SETTERS[attr] = method
        COLLECTED_SETTERS.clear()

    def __init__(self):
        super().__init__()
        self.name = self.NAME

        self.static_fields = {key: None for key in self.STATIC_FIELD_KEYS}

        self.parent_instances = [self.vm.get_class(parent.NAME, version=self.internal_version) for parent in
                                 self.PARENTS]

    def get_method(self, name: str, signature: str, inner=False) -> typing.Optional[typing.Callable]:
        if (name, signature) in self.METHODS: return self.METHODS[name, signature]

        for parent in self.parent_instances:
            m = parent.get_method(name, signature, inner=inner)
            if m is not None:
                return m

    def get_static_attribute(self, name: str, expected_type=None):
        if name in self.GETTERS:
            return self.GETTERS[name]()

        return self.static_fields[name]

    def set_static_attribute(self, name: str, value, descriptor=None):
        if name in self.SETTERS:
            self.SETTERS[name](value)
            return

        self.static_fields[name] = value

    def create_instance(self):
        return NativeClassInstance(self)

    def inject_method(self, name: str, signature: str, method, force=True):
        if force or (name, signature) not in self.METHODS:
            self.METHODS[(name, signature)] = method

    def is_subclass_of(self, class_name: str) -> bool:
        return self.name == class_name or any(cls.is_subclass_of(class_name) for cls in self.parent_instances)

    def get_dynamic_field_keys(self):
        return self.DYNAMIC_FIELD_KEYS

    def __repr__(self):
        return f"JavaNative({self.name})"


class NativeClassInstance(jvm.api.AbstractJavaClassInstance):
    def __init__(self, cls: Native):
        super().__init__()

        self.cls = cls
        self.fields = {name: None for name in cls.DYNAMIC_FIELD_KEYS}

    def get_field(self, name: str):
        if name not in self.fields: raise AttributeError(self, name)
        if name in self.cls.GETTERS: return self.cls.GETTERS[name](self)
        return self.fields[name]

    def set_field(self, name: str, value):
        if name not in self.fields: raise AttributeError(self, name)
        if name in self.cls.SETTERS:
            self.cls.SETTERS[name](self, value)
        else:
            self.fields[name] = value

    def get_method(self, name: str, signature: str):
        return self.cls.get_method(name, signature)

    def get_real_class(self) -> AbstractJavaClass:
        return self.cls


def native(name: str, signature: str, static: bool = False, private: bool = False):
    def register(method):
        method.name = name
        method.signature = signature
        method.access = (0x0008 if static else 0) | (0x0002 if private else 0x0001)

        COLLECTED_METHODS.append(method)

        return method

    return register


def getter(attr_name: str):
    def register(method):
        COLLECTED_GETTERS.append((attr_name, method))
        return method

    return register


def setter(attr_name: str):
    def register(method):
        COLLECTED_SETTERS.append((attr_name, method))
        return method

    return register


class MappedNative(Native):
    """
    Special sub-class of Native using a mapping
    """
    FIELD_MAPPING = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls.METHODS = {}
        cls.PARENTS = []

        for parent in cls.__bases__:
            if issubclass(parent, Native) and parent != Native:
                cls.PARENTS.append(parent)

        for method in COLLECTED_METHODS:
            ind = method.name, method.signature
            cls.METHODS[ind] = method

            if cls.NAME in METHOD_MAPPING and ind in METHOD_MAPPING[cls.NAME]:
                new_name = METHOD_MAPPING[cls.NAME][ind]

                if isinstance(new_name, str):
                    cls.METHODS[new_name, method.signature] = method
                else:
                    for name in new_name:
                        cls.METHODS[name, method.signature] = method

        COLLECTED_METHODS.clear()

        if cls.NAME in FIELD_MAPPING:
            cls.FIELD_MAPPING = FIELD_MAPPING[cls.NAME]

    def __init__(self):
        super().__init__()

        if self.name in CLASS_MAPPING:
            original_name = self.name
            self.name = CLASS_MAPPING[self.name]

            self.vm.shared_classes[original_name] = self

    def get_static_attribute(self, name: str, expected_type=None):
        if name in self.FIELD_MAPPING: name = self.FIELD_MAPPING[name]

        return self.static_fields[name]

    def set_static_attribute(self, name: str, value, descriptor=None):
        if name in self.FIELD_MAPPING: name = self.FIELD_MAPPING[name]

        self.static_fields[name] = value


CLASS_MAPPING: typing.Dict[str, str] = {}
METHOD_MAPPING: typing.Dict[str, typing.Dict[typing.Tuple[str, str], typing.Union[str, typing.Iterable[str]]]] = {}
FIELD_MAPPING: typing.Dict[str, typing.Dict[str, str]] = {}


class Instance(NativeClassInstance):
    """
    Wrapper class for defining the instance of a java class
    """
    PROTECT = True

    @classmethod
    def __class_getitem__(cls, item: typing.Union[Native, type, str]) -> type:
        return NativeClassInstance if isinstance(item, str) or issubclass(item, Native) else item


class Array:
    @classmethod
    def __class_getitem__(cls, item: typing.Union[Native, type, typing.Tuple[type, str]]):
        return typing.List[Instance[item]]

