from mcpython import shared
from jvm.Java import NativeClass, native


class Cipher(NativeClass):
    NAME = "javax/crypto/Cipher"

    @native("getMaxAllowedKeyLength", "(Ljava/lang/String;)I")
    def getMaxAllowedKeyLength(self, *_):
        return 10
