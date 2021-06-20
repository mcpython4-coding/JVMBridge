from mcpython import shared
from jvm.Java import NativeClass, native


class Proxy(NativeClass):
    NAME = "java/lang/reflect/Proxy"

    @native("newProxyInstance",
            "(Ljava/lang/ClassLoader;[Ljava/lang/Class;Ljava/lang/reflect/InvocationHandler;)Ljava/lang/Object;")
    def newProxyInstance(self, loader, interfaces, invocation_handler):
        instance = self.create_instance()
        return instance

    @native("getClass", "()Ljava/lang/Class;")
    def getClass(self, *_):
        pass

