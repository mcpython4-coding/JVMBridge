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
from jvm.Java import NativeClass, native


class LinkedHashSet(NativeClass):
    NAME = "java/util/LinkedHashSet"

    def create_instance(self):
        return set()

    @native("<init>", "()V")
    def init(self, *_):
        pass

    @native("add", "(Ljava/lang/Object;)Z")
    def add(self, instance, obj):
        instance.add(obj)
        return instance

    @native("iterator", "()Ljava/util/Iterator;")
    def iterator(self, instance):
        return list(instance)
