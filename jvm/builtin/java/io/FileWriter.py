from mcpython import shared
from jvm.Java import NativeClass, native


class FileWriter(NativeClass):
    NAME = "java/io/FileWriter"

    @native("<init>", "(Ljava/io/File;)V")
    def init(self, *_):
        pass

    @native("write", "(Ljava/lang/String;)V")
    def write(self, *_):
        pass

    @native("close", "()V")
    def close(self, *_):
        pass
