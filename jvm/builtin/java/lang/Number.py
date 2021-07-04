from mcpython import shared
from jvm.Java import NativeClass, native


class Number(NativeClass):
    NAME = "java/lang/Number"

    @native("longValue", "()J")
    def longValue(self, instance):
        return int(instance)

