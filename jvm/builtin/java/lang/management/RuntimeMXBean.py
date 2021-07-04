from mcpython import shared
from jvm.Java import NativeClass, native


class RuntimeMXBean(NativeClass):
    NAME = "java/lang/management/RuntimeMXBean"

    @native("getInputArguments", "()Ljava/util/List;")
    def getInputArguments(self, *_):
        return []
