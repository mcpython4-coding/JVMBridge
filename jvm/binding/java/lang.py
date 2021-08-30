from jvm.builtinwrapper import handler as builtin_handler
import jvm.exceptions


@builtin_handler.bind_method("java/lang/Objects:requireNonNull(Ljava/lang/Object;)Ljava/lang/Object;")
def requireNonNull(obj):
    if obj is None:
        raise jvm.exceptions.NullPointerException

    return obj

