from jvm.builtinwrapper import handler as builtin_handler
import jvm.exceptions


@builtin_handler.bind_method("java/lang/Objects:requireNonNull(Ljava/lang/Object;)Ljava/lang/Object;")
def requireNonNull(obj):
    if obj is None:
        raise jvm.exceptions.NullPointerException

    return obj


@builtin_handler.bind_method("java/lang/Enum:name()Ljava/lang/String;")
def name(self):
    if isinstance(self, str):
        return self.split("::")[-1]

    if hasattr(self, "get_class"):
        cls = self.get_class()

        for key, value in cls.static_field_values.items():
            if value == self:
                return key

    return str(self)

