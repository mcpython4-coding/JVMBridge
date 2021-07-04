from mcpython import shared
from jvm.Java import NativeClass, native


class ConcurrentLinkedQueue(NativeClass):
    NAME = "java/util/concurrent/ConcurrentLinkedQueue"

    @native("<init>", "()V")
    def init(self, *_):
        pass
