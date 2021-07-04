from mcpython import shared
from jvm.Java import NativeClass, native


class ConcurrentMap(NativeClass):
    NAME = "java/util/concurrent/ConcurrentMap"

    def create_instance(self):
        return {}

    @native("computeIfAbsent", "(Ljava/lang/Object;Ljava/util/function/Function;)Ljava/lang/Object;")
    def computeIfAbsent(self, instance, key, supplier):
        if key not in instance:
            instance[key] = supplier()
        return instance[key]
