from mcpython import shared
from jvm.Java import NativeClass, native, AbstractJavaClass


class MethodHandles(NativeClass):
    NAME = "java/lang/invoke/MethodHandles"

    @native("lookup", "()Ljava/lang/invoke/MethodHandles$Lookup;")
    def lookup(self, *_):
        pass


class MethodHandles__Lookup(NativeClass):
    NAME = "java/lang/invoke/MethodHandles$Lookup"

    @native("lookupClass", "()Ljava/lang/Class;")
    def lookupClass(self, instance):
        return instance[1]

    @native("findStatic", "(Ljava/lang/Class;Ljava/lang/String;Ljava/lang/invoke/MethodType;)Ljava/lang/invoke/MethodHandle;")
    def findStatic(self, instance, cls: AbstractJavaClass, name, method_type):
        return cls.get_method(name, instance[2][0][2][2][1])

    @native("unreflectGetter", "(Ljava/lang/reflect/Field;)Ljava/lang/invoke/MethodHandle;")
    def unreflectGetter(self, instance, field):
        pass

