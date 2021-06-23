from mcpython import shared
from jvm.Java import NativeClass, native


class Long(NativeClass):
    NAME = "java/lang/Long"

    @native("valueOf", "(J)Ljava/lang/Long;")
    def valueOf(self, instance):
        return instance

