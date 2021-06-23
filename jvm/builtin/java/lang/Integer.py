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


class Integer(NativeClass):
    NAME = "java/lang/Integer"

    @native("valueOf", "(I)Ljava/lang/Integer;")
    def valueOf(self, instance):
        return instance

    @native("toString", "(I)Ljava/lang/String;")
    def toString(self, instance):
        return str(instance)

    @native("intValue", "()I")
    def intValue(self, instance):
        return instance
