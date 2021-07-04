from mcpython import shared
from jvm.Java import NativeClass, native
import jvm.RuntimeModificationUtil
from jvm.Runtime import InvokeSpecial, BytecodeRepr


# This is needed, as we cannot do something like this in a constructor
# We use a normal InvokeVirtual instruction internally as we have an instance floating around on the stack
BytecodeRepr.MODIFICATION_ITERATIONS.append(
    jvm.RuntimeModificationUtil.create_method_relocator(
        ("java/long/Long", "<init>", "(Ljava/lang/String;)V"),
        ("java/lang/Long", "fromString", "(Ljava/lang/String;)Ljava/lang/Long;"),
        ground_type=InvokeSpecial,
    )
)


class Long(NativeClass):
    NAME = "java/lang/Long"

    def create_instance(self):
        return 0

    @native("<init>", "(Ljava/lang/String;)V")
    def init(self, *_):
        pass  # todo: add a optimiser iteration to fix this

    @native("valueOf", "(J)Ljava/lang/Long;")
    def valueOf(self, instance):
        return instance

    @native("longValue", "()J")
    def longValue(self, instance):
        return instance

    @native("toString", "(J)Ljava/lang/String;")
    def toString(self, instance):
        return str(instance)

    @native("fromString", "(Ljava/lang/String;)Ljava/lang/Long;")
    def fromString(self, _, string):
        return int(string)

