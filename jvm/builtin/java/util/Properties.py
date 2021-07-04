from mcpython import shared
from jvm.Java import NativeClass, native


class Properties(NativeClass):
    NAME = "java/util/Properties"

    @native("<init>", "()V")
    def init(self, instance):
        instance.table = {}

    @native("<init>", "(Ljava/util/Properties;)V")
    def init2(self, instance, properties):
        instance.table = properties.table.copy()

    @native("setProperty", "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/Object;")
    def setProperty(self, instance, key, value):
        instance.table[key] = value
        return instance

    @native("getProperty", "(Ljava/lang/String;)Ljava/lang/String;")
    def getProperty(self, instance, key):
        return instance.table[key]

    @native("load", "(Ljava/io/Reader;)V")
    def load(self, instance, reader):
        pass
