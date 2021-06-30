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


class Object2FloatMap(NativeClass):
    NAME = "it/unimi/dsi/fastutil/objects/Object2FloatMap"

    @native("put", "(Ljava/lang/Object;F)F")
    def put(self, instance, key, value):
        return value


class Byte2ObjectArrayMap(NativeClass):
    NAME = "it/unimi/dsi/fastutil/bytes/Byte2ObjectArrayMap"

    def create_instance(self):
        return {}

    @native("<init>", "(I)V")
    def init(self, instance, size):
        pass

    @native("put", "(BLjava/lang/Object;)Ljava/lang/Object;")
    def put(self, instance, key, value):
        instance.setdefault(key, []).append(value)
        return value


class ObjectOpenHashSet(NativeClass):
    NAME = "it/unimi/dsi/fastutil/objects/ObjectOpenHashSet"

    @native("<init>", "()V")
    def init(self, instance):
        instance.underlying = set()


class Object2IntOpenHashMap(NativeClass):
    NAME = "it/unimi/dsi/fastutil/objects/Object2IntOpenHashMap"

    def create_instance(self):
        return {}

    @native("<init>", "()V")
    def init(self, instance):
        pass


class Object2ObjectOpenHashMap(NativeClass):
    NAME = "it/unimi/dsi/fastutil/objects/Object2ObjectOpenHashMap"

    def create_instance(self):
        return {}

    @native("<init>", "()V")
    def init(self, *_):
        pass


class Reference2ReferenceOpenHashMap(NativeClass):
    NAME = "it/unimi/dsi/fastutil/objects/Reference2ReferenceOpenHashMap"

    def create_instance(self):
        return {}

    @native("<init>", "()V")
    def init(self, *_):
        pass


class Byte2ObjectMap(NativeClass):
    NAME = "it/unimi/dsi/fastutil/bytes/Byte2ObjectMap"

    def create_instance(self):
        return {}

    @native("put", "(BLjava/lang/Object;)Ljava/lang/Object;")
    def put(self, instance, key, value):
        instance[key] = value
        return value
