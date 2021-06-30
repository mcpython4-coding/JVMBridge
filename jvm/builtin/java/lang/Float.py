from mcpython import shared
from jvm.Java import NativeClass, native


class Float(NativeClass):
    NAME = "java/lang/Float"

    @native("valueOf", "(F)Ljava/lang/Float;")
    def valueOf(self, instance):
        return instance

    @native("floatValue", "()F")
    def floatValue(self, instance):
        return instance
