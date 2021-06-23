from mcpython import shared
from jvm.Java import NativeClass, native


class Constructor(NativeClass):
    NAME = "java/lang/reflect/Constructor"

    @native("newInstance", "([Ljava/lang/Object;)Ljava/lang/Object;")
    def newInstance(self, instance, args):
        return instance.create_instance()  # todo: implement constructor call

