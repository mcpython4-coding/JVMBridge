from mcpython import shared
from jvm.Java import NativeClass, native


class FileReader(NativeClass):
    NAME = "java/io/FileReader"

    @native("<init>", "(Ljava/lang/String;)V")
    def init(self, instance, path: str):
        instance.stream = open(path)

    @native("close", "()V")
    def close(self, instance):
        instnace.stream.close()
