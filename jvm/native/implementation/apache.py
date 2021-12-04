from jvm.natives import bind_native, bind_annotation


class Pair:
    @staticmethod
    @bind_native("org/apache/commons/lang3/tuple/Pair", "getRight()Ljava/lang/Object;")
    @bind_native("org/apache/commons/lang3/tuple/Pair", "getValue()Ljava/lang/Object;")
    def getRight(method, stack, this):
        return this[1]

    @staticmethod
    @bind_native("org/apache/commons/lang3/tuple/Pair", "getLeft()Ljava/lang/Object;")
    @bind_native("org/apache/commons/lang3/tuple/Pair", "getKey()Ljava/lang/Object;")
    def getLeft(method, stack, this):
        return this[0]

    @staticmethod
    @bind_native("org/apache/commons/lang3/tuple/Pair", "of(Ljava/lang/Object;Ljava/lang/Object;)Lorg/apache/commons/lang3/tuple/Pair;")
    def createFromTwo(method, stack, a, b):
        return a, b

