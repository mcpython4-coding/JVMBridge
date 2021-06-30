import typing

from jvm.Java import AbstractJavaClass


REGISTERED_NATIVES = set()

COLLECTED_METHODS = []


class Native(AbstractJavaClass):
    NAME = None

    IS_ABSTRACT = False
    IS_INTERFACE = False

    METHODS = None
    DYNAMIC_FIELD_KEYS = set()
    STATIC_FIELD_KEYS = set()

    PARENTS = None

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls.METHODS = {}
        cls.PARENTS = []

        for parent in cls.__bases__:
            if issubclass(parent, Native) and parent != Native:
                cls.PARENTS.append(parent)

        for method in COLLECTED_METHODS:
            cls.METHODS[method.name, method.signature] = method
        COLLECTED_METHODS.clear()

    def __init__(self):
        super().__init__()
        self.name = self.NAME

        self.static_fields = {key: None for key in self.STATIC_FIELD_KEYS}

        self.parent_instances = [self.vm.get_class(parent.NAME, version=self.internal_version) for parent in self.PARENTS]

    def get_method(self, name: str, signature: str, inner=False) -> typing.Optional[typing.Callable]:
        if (name, signature) in self.METHODS: return self.METHODS[name, signature]

        for parent in self.parent_instances:
            m = parent.get_method(name, signature, inner=inner)
            if m is not None:
                return m

    def get_static_attribute(self, name: str, expected_type=None):
        return self.static_fields[name]

    def set_static_attribute(self, name: str, value):
        self.static_fields[name] = value

    def create_instance(self):
        pass

    def inject_method(self, name: str, signature: str, method, force=True):
        if force or (name, signature) not in self.METHODS:
            self.METHODS[(name, signature)] = method

    def is_subclass_of(self, class_name: str) -> bool:
        return self.name == class_name or any(cls.is_subclass_of(class_name) for cls in self.parent_instances)

    def get_dynamic_field_keys(self):
        return self.DYNAMIC_FIELD_KEYS


def native(name: str, signature: str, static: bool = False, private: bool = False):
    def register(method):
        method.name = name
        method.signature = signature
        method.access = (0x0008 if static else 0) | (0x0002 if private else 0x0001)

        COLLECTED_METHODS.append(method)

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

    def set_static_attribute(self, name: str, value):
        if name in self.FIELD_MAPPING: name = self.FIELD_MAPPING[name]

        self.static_fields[name] = value


CLASS_MAPPING: typing.Dict[str, str] = {}
METHOD_MAPPING: typing.Dict[str, typing.Dict[typing.Tuple[str, str], typing.Union[str, typing.Iterable[str]]]] = {}
FIELD_MAPPING: typing.Dict[str, typing.Dict[str, str]] = {}

