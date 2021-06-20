from mcpython import shared
from jvm.Java import NativeClass, native


class SafeVarargs(NativeClass):
    NAME = "java/lang/SafeVarargs"

    def on_annotate(self, cls, args):
        pass

