from mcpython import shared
from jvm.Java import NativeClass, native


class BiConsumer(NativeClass):
    NAME = "java/util/function/BiConsumer"

    @native("accept", "(Ljava/lang/Object;Ljava/lang/Object;)V")
    def accept(self, instance, a, b):
        instance(a, b)
