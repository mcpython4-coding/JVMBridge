from mcpython import shared
from jvm.Java import NativeClass, native


class ManagementFactory(NativeClass):
    NAME = "java/lang/management/ManagementFactory"

    @native("getRuntimeMXBean", "()Ljava/lang/management/RuntimeMXBean;")
    def getRuntimeMXBean(self, *_):
        pass
