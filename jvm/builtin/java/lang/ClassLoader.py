from mcpython import shared, logger
from jvm.Java import NativeClass, native
import io
import mcpython.ResourceLoader


class ClassLoader(NativeClass):
    NAME = "java/lang/ClassLoader"

    @native("loadClass", "(Ljava/lang/String;)Ljava/lang/Class;")
    def loadClass(self, instance, name):
        return instance.get_class(name)

    @native("getResourceAsStream", "(Ljava/lang/String;)Ljava/io/InputStream;")
    def getResourceAsStream(self, instance, path: str):
        try:
            return io.BytesIO(mcpython.ResourceLoader.read_raw(path))
        except:
            logger.print_exception("reading exception")
            return io.BytesIO(bytes())

