from mcpython import shared
from jvm.Java import NativeClass, native


class Nullable(NativeClass):
    NAME = "javax/annotation/Nullable"

    def on_annotate(self, cls, args):
        pass


class Nullable2(NativeClass):
    NAME = "edu/umd/cs/findbugs/annotations/Nullable"

    def on_annotate(self, cls, args):
        pass

