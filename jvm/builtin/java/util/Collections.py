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
from jvm.JavaExceptionStack import StackCollectingException


class Collections(NativeClass):
    NAME = "java/util/Collections"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "EMPTY_LIST": [],
        })

    @native("addAll", "(Ljava/util/Collection;[Ljava/lang/Object;)Z")
    def addAll(self, collection, objects):
        pass  # todo: implement

    @native("unmodifiableList", "(Ljava/util/List;)Ljava/util/List;")
    def unmodifiableList(self, array):
        return tuple(array)

    @native("unmodifiableSet", "(Ljava/util/Set;)Ljava/util/Set;")
    def unmodifiableSet(self, instance):
        return instance  # todo: make mutable

    @native("emptyList", "()Ljava/util/List;")
    def emptyList(self):
        return []

    @native("emptyMap", "()Ljava/util/Map;")
    def emptyMap(self):
        return {}

    @native("singletonList", "(Ljava/lang/Object;)Ljava/util/List;")
    def singletonList(self, obj):
        return obj,

    @native("newSetFromMap", "(Ljava/util/Map;)Ljava/util/Set;")
    def newSetFromMap(self, m):
        try:
            return set(m.keys())
        except:
            raise StackCollectingException(m)

    @native("synchronizedList", "(Ljava/util/List;)Ljava/util/List;")
    def synchronizedList(self, array):
        return array

    @native("sort", "(Ljava/util/List;)V")
    def sort(self, instance):
        return list(sorted(instance))

    @native("unmodifiableMap", "(Ljava/util/Map;)Ljava/util/Map;")
    def unmodifiableMap(self, data):
        return data.copy()
