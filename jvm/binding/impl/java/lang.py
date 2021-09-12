from jvm import builtinwrapper
from jvm.api import AbstractJavaClass
from jvm.builtinwrapper import handler as builtin_handler
import jvm.exceptions


@builtin_handler.bind_method("java/lang/Objects:requireNonNull(Ljava/lang/Object;)Ljava/lang/Object;")
def requireNonNull(obj):
    if obj is None:
        raise jvm.exceptions.NullPointerException("Encountered 'null', expected non-null; See trace for what is null")

    return obj


@builtin_handler.bind_method("java/lang/Enum:name()Ljava/lang/String;")
def name(self):
    if isinstance(self, str):
        return self.split("::")[-1]

    # todo: add a better lookup method!
    if hasattr(self, "get_class"):
        cls = self.get_class()

        for key, value in cls.static_field_values.items():
            if value == self:
                return key

    return str(self)


@builtin_handler.bind_method("java/lang/Class:getEnumConstants()[Ljava/lang/Object;")
def getEnumConstants(self: AbstractJavaClass):
    return [self.get_static_attribute(n) for n in self.enum_fields]


@builtin_handler.bind_method("java/util/List:removeIf(Ljava/util/function/Predicate;)Z")
def removeIf(instance: list, predicate):
    d = instance[:]
    instance.clear()
    instance.extend(e for e in d if predicate(e))
    return 1

