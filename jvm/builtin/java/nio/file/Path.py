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
import os

from mcpython import shared
from jvm.Java import NativeClass, native


class Path(NativeClass):
    NAME = "java/nio/file/Path"

    @native("toAbsolutePath", "()Ljava/nio/file/Path;")
    def toAbsolutePath(self, instance):
        return instance

    @native("toString", "()Ljava/lang/String;")
    def toString(self, instance):
        return str(instance)

    @native("toFile", "()Ljava/io/File;")
    def toFile(self, instance):
        obj = self.vm.get_class("java/io/File", version=self.internal_version)
        obj.path = instance.path if instance is not None else None
        return obj

    @native("resolve", "(Ljava/lang/String;)Ljava/nio/file/Path;")
    def resolve(self, instance, path: str):
        obj = self.create_instance()
        obj.path = (instance.path if not isinstance(instance, str) else instance) + "/" + path
        return obj

    @native("getParent", "()Ljava/nio/file/Path;")
    def getParent(self, instance):
        obj = self.create_instance()
        obj.path = os.path.dirname(instance if isinstance(instance, str) else instance.path)
        return obj
