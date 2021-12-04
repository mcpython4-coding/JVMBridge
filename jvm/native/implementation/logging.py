import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.natives import bind_native, bind_annotation


@bind_native("org/apache/logging/log4j/LogManager", "getLogger()Lorg/apache/logging/log4j/Logger;")
@bind_native("org/apache/logging/log4j/LogManager", "getLogger(Ljava/lang/String;)Lorg/apache/logging/log4j/Logger;")
@bind_native("org/apache/logging/log4j/LogManager", "getLogger(Ljava/lang/Class;)Lorg/apache/logging/log4j/Logger;")
@bind_native("org/apache/logging/log4j/core/LoggerContext", "getLogger(Ljava/lang/String;)Lorg/apache/logging/log4j/core/Logger;")
@bind_native("org/apache/logging/log4j/LogManager", "getRootLogger()Lorg/apache/logging/log4j/Logger;")
def getLogger(method, stack, name_or_obj=None, name=None):
    pass


@bind_native("org/apache/logging/log4j/core/Logger", "getContext()Lorg/apache/logging/log4j/core/LoggerContext;")
def getContext(method, stack, this):
    pass


@bind_native("org/apache/logging/log4j/MarkerManager", "getMarker(Ljava/lang/String;)Lorg/apache/logging/log4j/Marker;")
def getMarker(method, stack, name: str):
    pass


@bind_native("org/apache/logging/log4j/core/Logger", "getLevel()Lorg/apache/logging/log4j/Level;")
def getLevel(method, stack, this):
    return "NORMAL"


@bind_native("org/apache/logging/log4j/core/Logger", "setLevel(Lorg/apache/logging/log4j/Level;)V")
def setLevel(method, stack, this, level):
    pass


@bind_native("org/apache/logging/log4j/Logger", "info(Ljava/lang/String;)V")
def info(method, stack, this, arg: str):
    print("[JVM][INFO]", arg)


@bind_native("org/apache/logging/log4j/Logger", "info(Ljava/lang/String;Ljava/lang/Object;)V")
def infoWithObject(method, stack, this, arg, obj):
    print("[JVM][INFO]", arg, obj)


@bind_native("org/apache/logging/log4j/Logger", "error(Ljava/lang/String;)V")
def error(method, stack, this, arg):
    print("[JVM][ERROR]", arg)


@bind_native("org/apache/logging/log4j/Logger", "error(Ljava/lang/String;Ljava/lang/Object;)V")
def error(method, stack, this, arg, obj):
    print("[JVM][ERROR]", arg, obj)


@bind_annotation("org/apache/logging/log4j/core/config/plugins/Plugin")
def no_action(*args):
    pass

