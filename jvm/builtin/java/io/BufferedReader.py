from mcpython import shared
from jvm.Java import NativeClass, native


class BufferedReader(NativeClass):
    NAME = "java/io/BufferedReader"

    @native("<init>", "(Ljava/io/Reader;)V")
    def init(self, *_):
        pass

    @native("lines", "()Ljava/util/stream/Stream;")
    def lines(self, *_):
        return []

