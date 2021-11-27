from jvm.natives import bind_native, bind_annotation


class Pair:
    @staticmethod
    @bind_native("org/apache/commons/lang3/tuple/Pair", "getRight()Ljava/lang/Object;")
    def getRight(method, stack, this):
        return this[1]

    @staticmethod
    @bind_native("org/apache/commons/lang3/tuple/Pair", "getLeft()Ljava/lang/Object;")
    def getLeft(method, stack, this):
        return this[0]

