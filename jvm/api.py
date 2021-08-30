import sys
import typing
from abc import ABC
from abc import ABCMeta
from abc import abstractmethod

vm = None


class AbstractJavaClass:
    """
    Abstract base class for java classes handled by the vm
    """

    def __init__(self):
        self.name: str = None  # the class name
        self.file_source: str = None  # a path to the file this class was loaded from
        self.parent = None  # the parent of the class
        self.interfaces: typing.List[
            typing.Callable[[], typing.Optional[AbstractJavaClass]]
        ] = []
        self.internal_version = None  # the internal version identifier
        self.vm = None  # the vm instance bound to

    def get_method(self, name: str, signature: str, inner=False):
        raise NotImplementedError

    def get_static_attribute(self, name: str, expected_type=None):
        raise NotImplementedError

    def set_static_attribute(self, name: str, value):
        raise NotImplementedError

    def create_instance(self):
        raise NotImplementedError

    def inject_method(self, name: str, signature: str, method, force=True):
        raise NotImplementedError

    def on_annotate(self, obj, args):
        print(f"missing annotation implementation on {self} annotating {obj} with {args}")

    def get_dynamic_field_keys(self):
        return set()

    def is_subclass_of(self, class_name: str) -> bool:
        raise NotImplementedError

    def prepare_use(self, runtime=None):
        pass


class AbstractJavaClassInstance(ABC):
    def get_field(self, name: str):
        raise NotImplementedError

    def set_field(self, name: str, value):
        raise NotImplementedError

    def get_method(self, name: str, signature: str):
        raise NotImplementedError

    def get_class(self) -> AbstractJavaClass:
        raise NotImplementedError


DYNAMIC_NATIVES = "--fill-unknown-natives" in sys.argv


class AbstractMethod(metaclass=ABCMeta):
    def __init__(self):
        self.class_file: AbstractJavaClass = None
        self.name: str = None
        self.signature: str = None
        self.access = 0
        self.code_repr = None

    @abstractmethod
    def invoke(self, args):
        pass

    @abstractmethod
    def get_class(self):
        pass

