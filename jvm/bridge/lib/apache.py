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


class Pair(NativeClass):
    """
    Represented by tuples
    """

    NAME = "org/apache/commons/lang3/tuple/Pair"

    @native("getLeft", "()Ljava/lang/Object;")
    def getLeft(self, instance):
        return instance[0]

    @native("getRight", "()Ljava/lang/Object;")
    def getRight(self, instance):
        return instance[1]


class IOUtils(NativeClass):
    NAME = "org/apache/commons/io/IOUtils"

    @native("closeQuietly", "(Ljava/io/Reader;)V")
    def closeQuietly(self, reader):
        pass

    @native("closeQuietly", "(Ljava/io/InputStream;)V")
    def closeQuietly2(self, stream):
        pass
