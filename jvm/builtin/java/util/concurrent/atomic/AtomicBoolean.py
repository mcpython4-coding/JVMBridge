from mcpython import shared
from jvm.Java import NativeClass, native


class AtomicBoolean(NativeClass):
    NAME = "java/util/concurrent/atomic/AtomicBoolean"

    @native("<init>", "()V")
    def init(self, *_):
        pass