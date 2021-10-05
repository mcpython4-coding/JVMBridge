import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.natives import bind_native, bind_annotation


@bind_native("org/apache/logging/log4j/LogManager", "getLogger()Lorg/apache/logging/log4j/Logger;")
@bind_native("org/apache/logging/log4j/LogManager", "getLogger(Ljava/lang/String;)Lorg/apache/logging/log4j/Logger;")
@bind_native("org/apache/logging/log4j/LogManager", "getLogger(Ljava/lang/Class;)Lorg/apache/logging/log4j/Logger;")
def getLogger(method, stack, name=None):
    pass


@bind_native("org/apache/logging/log4j/core/Logger", "getLevel()Lorg/apache/logging/log4j/Level;")
def getLevel(method, stack, this):
    return "NORMAL"


@bind_native("org/apache/logging/log4j/core/Logger", "setLevel(Lorg/apache/logging/log4j/Level;)V")
def setLevel(method, stack, this):
    pass

