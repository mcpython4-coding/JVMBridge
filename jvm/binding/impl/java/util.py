from jvm.builtinwrapper import handler as builtin_handler


class ServiceLoader:
    # See https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/ServiceLoader.html for reference

    @staticmethod
    @builtin_handler.bind_method("java/util/ServiceLoader:load(Ljava/lang/Class;)Ljava/util/ServiceLoader;")
    def load(cls):
        pass

