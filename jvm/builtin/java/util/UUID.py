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
import uuid

from mcpython import shared
from jvm.Java import NativeClass, native


class UUID(NativeClass):
    NAME = "java/util/UUID"

    @native("<init>", "(JJ)V")
    def init(self, instance):
        pass

    @native("fromString", "(Ljava/lang/String;)Ljava/util/UUID;", static=True)
    def fromString(self, string):
        return uuid.UUID(string)

    @native("randomUUID", "()Ljava/util/UUID;", static=True)
    def randomUUID(self):
        return uuid.uuid4()

    @native("toString", "()Ljava/lang/String;")
    def toString(self, instance: uuid.UUID):
        return instance.urn
