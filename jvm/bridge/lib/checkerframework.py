from mcpython import shared
from jvm.Java import NativeClass, native


class EnsuresNonNullIf(NativeClass):
    NAME = "org/checkerframework/checker/nullness/qual/EnsuresNonNullIf"

    def on_annotate(self, cls, args):
        pass


class Pure(NativeClass):
    NAME = "org/checkerframework/dataflow/qual/Pure"


class SideEffectFree(NativeClass):
    NAME = "org/checkerframework/dataflow/qual/SideEffectFree"

