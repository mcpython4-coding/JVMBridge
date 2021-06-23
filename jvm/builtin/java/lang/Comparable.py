from mcpython import shared
from jvm.Java import NativeClass, native


class Comparable(NativeClass):
    NAME = "java/lang/Comparable"

    @native("compareTo", "(Ljava/lang/Object;)I")
    def compareTo(self, instance, other):
        return int(instance == other)

