from mcpython import shared
from jvm.Java import NativeClass, native


class InputStreamReader(NativeClass):
    NAME = "java/io/InputStreamReader"

    @native("<init>", "(Ljava/io/InputStream;Ljava/nio/charset/Charset;)V")
    def init(self, instance, stream, charset):
        instance.stream = stream
        instance.charset = charset

    def read_stuff(self, instance):
        return instance.stream.read().decode(instance.charset)

