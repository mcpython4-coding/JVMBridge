from mcpython import shared
from jvm.Java import NativeClass, native, NativeClassInstance


class ConstantCallSiteInstance(NativeClassInstance):
    def __call__(self, *args, **kwargs):
        pass


class ConstantCallSite(NativeClass):
    NAME = "java/lang/invoke/ConstantCallSite"

    def create_instance(self):
        return ConstantCallSiteInstance(self)

    @native("<init>", "(Ljava/lang/invoke/MethodHandle;)V")
    def init(self, instance, handle):
        pass

