from mcpython import shared
from mcpython.engine import logger
from jvm.Java import NativeClass, native


class PrintStream(NativeClass):
    NAME = "java/io/PrintStream"

    @native("println", "(Ljava/lang/String;)V")
    def println(self, instance, text):
        logger.println("[JVM][OUT]", text)

