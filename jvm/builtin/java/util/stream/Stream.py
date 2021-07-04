"""
mcpython - a minecraft clone written in python licenced under the MIT-licence 
(https://github.com/mcpython4-coding/core)

Contributors: uuk, xkcdjerry (inactive)

Based on the game of fogleman (https://github.com/fogleman/Minecraft), licenced under the MIT-licence
Original game "minecraft" by Mojang Studios (www.minecraft.net), licenced under the EULA
(https://account.mojang.com/documents/minecraft_eula)
Mod loader inspired by "Minecraft Forge" (https://github.com/MinecraftForge/MinecraftForge) and similar

This project is not official by mojang and does not relate to it.
"""
from jvm.Java import NativeClass, native


class Stream(NativeClass):
    NAME = "java/util/stream/Stream"

    @native("filter", "(Ljava/util/function/Predicate;)Ljava/util/stream/Stream;")
    def filter(self, instance, predicate):
        return instance

    @native("forEach", "(Ljava/util/function/Consumer;)V")
    def forEach(self, instance, consumer):
        try:
            for entry in instance:
                if callable(consumer):
                    consumer(entry)
                else:
                    consumer.inner(entry)
        except TypeError:
            pass

    @native("collect", "(Ljava/util/stream/Collector;)Ljava/lang/Object;")
    def collect(self, instance, collector):
        return collector(instance)

    @native("of", "([Ljava/lang/Object;)Ljava/util/stream/Stream;")
    def of(self, array):
        return array

    @native("of", "(Ljava/lang/Object;)Ljava/util/stream/Stream;")
    def of2(self, obj):
        return [obj]

    @native("map", "(Ljava/util/function/Function;)Ljava/util/stream/Stream;")
    def map(self, instance, function):
        return [function(e) for e in instance]

    @native(
        "concat",
        "(Ljava/util/stream/Stream;Ljava/util/stream/Stream;)Ljava/util/stream/Stream;",
    )
    def concat(self, a, b):
        return a + b

    @native("anyMatch", "(Ljava/util/function/Predicate;)Z")
    def anyMatch(self, instance, predicate):
        return int(any(predicate(e) for e in instance))

    @native("flatMap", "(Ljava/util/function/Function;)Ljava/util/stream/Stream;")
    def flatMap(self, instance, function):
        return [function(e) for e in instance]

    @native("toArray", "(Ljava/util/function/IntFunction;)[Ljava/lang/Object;")
    def toArray(self, instance, int_function):
        return list(instance)

    @native("sorted", "(Ljava/util/Comparator;)Ljava/util/stream/Stream;")
    def sorted(self, instance, comparator):
        return list(sorted(instance, key=comparator))

    @native("reduce", "(Ljava/util/function/BinaryOperator;)Ljava/util/Optional;")
    def reduce(self, instance, operator):
        result = None
        for e in instance:
            result = operator(result, e)
        return result

    @native("noneMatch", "(Ljava/util/function/Predicate;)Z")
    def noneMatch(self, stream, predicate):
        return not any(predicate(e) for e in stream)
