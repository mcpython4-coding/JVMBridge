from jvm.builtinwrapper import handler as builtin_handler
from jvm.exceptions import NullPointerException


@builtin_handler.bind_method("com/google/common/base/Preconditions:checkNotNull(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;")
def checkNotNull(obj, msg):
    if obj is None:
        raise NullPointerException(msg)
    return obj

