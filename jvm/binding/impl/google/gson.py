from jvm.api import AbstractJavaClass
from jvm.builtinwrapper import handler as builtin_handler
from jvm.api import AbstractJavaClassInstance


@builtin_handler.bind_method("com/google/gson/reflect/TypeToken:<init>()V")
def init(self: AbstractJavaClassInstance):
    self.fields["type"] = getSuperclassTypeParameter(self.get_class())


@builtin_handler.bind_method("com/google/gson/reflect/TypeToken:getSuperclassTypeParameter(Ljava/lang/Class;)Ljava/lang/reflect/Type;")
def getSuperclassTypeParameter(cls: AbstractJavaClass):
    signature = cls.attributes["Signature"][0].signature
    return cls.vm.get_class(signature.removeprefix("Lcom/google/gson/reflect/TypeToken<").removesuffix(">;"))


@builtin_handler.bind_method("com/google/gson/Gson:fromJson(Ljava/lang/String;Ljava/lang/reflect/Type;)Ljava/lang/Object;")
def fromJson(self, body, data_type: AbstractJavaClass):
    obj = data_type.create_instance()

    obj.get_method("<init>", "()V")(obj)

    return obj

