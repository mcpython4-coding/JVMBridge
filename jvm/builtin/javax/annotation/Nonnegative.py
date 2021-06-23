from mcpython import shared
from jvm.Java import NativeClass, native


class Nonnegative(NativeClass):
    NAME = "javax/annotation/Nonnegative"

    def on_annotate(self, cls, args):
        pass

