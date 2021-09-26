import sys

from jvm import builtinwrapper
from jvm.api import AbstractJavaClass
from jvm.builtinwrapper import handler as builtin_handler
import jvm.exceptions
import os


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


class System:
    home = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

    PROPERTIES = {
        "java.version": "17",
        "java.vendor": "uuk",
        "java.vendor.url": "www.github.com/uuk0",
        "java.home": home,
        "java.vm.specification.version": "17",
        "java.vm.specification.vendor": "oracle",
        "java.vm.specification.name": "oracle",
        "java.vm.version": "17",
        "java.vm.vendor": "uuk",
        "java.vm.name": "hotspot",
        "java.specification.version": "17",
        "java.specification.vendor": "oracle",
        "java.specification.name": "oracle",
        "java.class.version": "17",
        "java.class.path": home,
        "java.library.path": "",
        "java.io.tmpdir": home+"/tmp",
        "java.compiler": "none",
        "java.ext.dirs": home,
        "os.name": os.name,
        "os.arch": "x86",
        "os.version": "-1",
        "file.separator": os.sep,
        "path.separator": os.pathsep,
        "line.separator": os.linesep,
        "user.name": "unset",
        "user.home": home,
        "user.dir": home,

        "slf4j.detectLoggerNameMismatch": "",
    }

    @staticmethod
    @builtin_handler.bind_method("java/lang/System:setProperty(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;")
    def setProperty(key: str, value: str):
        System.PROPERTIES[key] = value

    @staticmethod
    @builtin_handler.bind_method("java/lang/System:getProperty(Ljava/lang/String;)Ljava/lang/String;")
    def getProperty(key: str):
        return System.PROPERTIES[key]

