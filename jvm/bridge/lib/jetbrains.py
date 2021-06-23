from mcpython import shared
from jvm.Java import NativeClass, native


class Nullable(NativeClass):
    NAME = "org/jetbrains/annotations/Nullable"

    def on_annotate(self, cls, args):
        pass


class NotNull(NativeClass):
    NAME = "org/jetbrains/annotations/NotNull"

    def on_annotate(self, cls, args):
        pass


class ApiStatus__NonExtendable(NativeClass):
    NAME = "org/jetbrains/annotations/ApiStatus$NonExtendable"

    def on_annotate(self, cls, args):
        pass


class ApiStatus__ScheduledForRemoval(NativeClass):
    NAME = "org/jetbrains/annotations/ApiStatus$ScheduledForRemoval"

    def on_annotate(self, cls, args):
        pass


class ApiStatus__Internal(NativeClass):
    NAME = "org/jetbrains/annotations/ApiStatus$Internal"

    def on_annotate(self, cls, args):
        pass


class ApiStatus__Experimental(NativeClass):
    NAME = "org/jetbrains/annotations/ApiStatus$Experimental"

    def on_annotate(self, cls, args):
        pass

