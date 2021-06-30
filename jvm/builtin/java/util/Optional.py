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
from mcpython import shared
from jvm.Java import JavaMethod, NativeClass, native
from jvm.JavaExceptionStack import StackCollectingException


class Optional(NativeClass):
    NAME = "java/util/Optional"

    @native("get", "()Ljava/lang/Object;")
    def get(self, instance):
        return instance

    @native("empty", "()Ljava/util/Optional;")
    def empty(self, *_):
        return self.create_instance()

    @native("filter", "(Ljava/util/function/Predicate;)Ljava/util/Optional;")
    def filter(self, instance, predicate):
        return None if instance is None or not predicate(instance) else instance

    @native("isPresent", "()Z")
    def isPresent(self, instance):
        return int(instance is None)

    @native("ifPresent", "(Ljava/util/function/Consumer;)V")
    def ifPresent(self, instance, consumer):
        if instance is not None:
            consumer(instance)

    @native("orElse", "(Ljava/lang/Object;)Ljava/lang/Object;")
    def orElse(self, instance, obj):
        return instance if instance is not None else obj
