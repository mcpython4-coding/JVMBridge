from mcpython import shared
from jvm.Java import NativeClass, native


class OverridingMethodsMustInvokeSuper(NativeClass):
    NAME = "javax/annotation/OverridingMethodsMustInvokeSuper"

    def on_annotate(self, cls, args):
        pass

