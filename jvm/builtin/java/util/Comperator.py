from mcpython import shared
from jvm.Java import NativeClass, native


class Comparator(NativeClass):
    NAME = "java/util/Comparator"

    @native("comparing", "(Ljava/util/function/Function;)Ljava/util/Comparator;", static=True)
    def comparing(self, function):
        return function

    @native("comparingLong", "(Ljava/util/function/ToLongFunction;)Ljava/util/Comparator;")
    def comparingLong(self, function):
        def compare(a, b):
            a = function(a)
            b = function(b)
            return 0 if a == b else (1 if a > b else -1)
        return compare

