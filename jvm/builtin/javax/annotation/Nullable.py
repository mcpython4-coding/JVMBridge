from mcpython import shared
from jvm.Java import NativeClass, native


class Nullable(NativeClass):
    NAME = "javax/annotation/Nullable"

    def on_annotate(self, cls, args):
        pass

