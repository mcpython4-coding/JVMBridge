import jvm.api
import jvm.Java


class ClassDecompiler:
    def __init__(self, cls: jvm.Java.JavaBytecodeClass):
        self.cls = cls

    def decompile(self, output_file: str):
        pass

