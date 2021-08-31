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

