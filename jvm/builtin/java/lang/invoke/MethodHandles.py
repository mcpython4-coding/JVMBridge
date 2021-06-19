from mcpython import shared
from jvm.Java import NativeClass, native, AbstractJavaClass


class MethodHandles__Lookup(NativeClass):
    NAME = "java/lang/invoke/MethodHandles$Lookup"

    @native("lookupClass", "()Ljava/lang/Class;")
    def lookupClass(self, instance):
        return instance[1]

    @native("findStatic", "(Ljava/lang/Class;Ljava/lang/String;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/MethodHandle;")
    def findStatic(self, instance, cls: AbstractJavaClass, name, method_type):
        return cls.get_method(name, instance[2][0][2][2][1])

