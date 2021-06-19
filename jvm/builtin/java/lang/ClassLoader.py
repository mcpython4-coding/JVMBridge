from mcpython import shared
from jvm.Java import NativeClass, native


class ClassLoader(NativeClass):
    NAME = "java/lang/ClassLoader"

    @native("loadClass", "(Ljava/lang/String;)Ljava/lang/Class;")
    def loadClass(self, instance, name):
        return instance.get_class(name)

