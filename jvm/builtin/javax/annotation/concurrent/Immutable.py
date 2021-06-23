from mcpython import shared
from jvm.Java import NativeClass, native


class Immutable(NativeClass):
    NAME = "javax/annotation/concurrent/Immutable"

    def on_annotate(self, cls, args):
        pass

