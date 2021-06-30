from mcpython import shared
from jvm.Java import NativeClass, native


class InputStream(NativeClass):
    NAME = "java/io/InputStream"

    @native("close", "()V")
    def close(self, *_):
        pass
