from mcpython import shared
from jvm.Java import NativeClass, native


class Runnable(NativeClass):
    NAME = "java/lang/Runnable"

    @native("run", "()V")
    def run(self, instance):
        instance()
