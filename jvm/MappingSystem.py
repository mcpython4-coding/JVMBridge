from abc import ABC
from jvm.api import AbstractJavaVM
import jvm.Java


class AbstractMapping(ABC):
    """
    Class defining how mappings can be looked up
    """

    def map_class_name(self, source_name: str) -> str:
        return source_name

    def map_method_name(self, cls_name: str, method_name: str, signature: str) -> str:
        return method_name

    def map_attribute_name(self, cls_name: str, attribute_name: str, signature: str) -> str:
        return attribute_name

    def map_parameter_name(self, cls_name: str, method_name: str, signature: str, unmapped_name: str, parameter_number: int) -> str:
        return unmapped_name

    def map_local_variable(self, cls_name: str, method_name: str, signature: str, unmapped_name: str, local_var_index_number: int) -> str:
        return unmapped_name


class MappingApplier:
    def __init__(self, vm: AbstractJavaVM, mapper: AbstractMapping):
        self.vm = vm
        self.mapper = mapper

    def walk(self):
        for cls in self.vm.walk_across_classes():
            if isinstance(cls, jvm.Java.JavaBytecodeClass):
                self.process_class(cls)

    def process_class(self, cls: jvm.Java.JavaBytecodeClass):
        for data in cls.cp:
            tag = data[0]

            # Class ref
            if tag == 7:
                pass

