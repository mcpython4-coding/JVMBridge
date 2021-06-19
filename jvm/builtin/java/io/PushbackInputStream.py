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


class PushbackInputStream(NativeClass):
    NAME = "java/io/PushbackInputStream"

    @native("<init>", "(Ljava/io/InputStream;I)V")
    def init(self, instance, stream, size):
        instance.data = stream.underlying.read()
        instance.size = size
        instance.offset = 0

    @native("read", "([BII)I")
    def read(self, instance, buffer, start, end):
        buffer[:] = instance.data[start + instance.offset : end + instance.offset]
        instance.offset += len(buffer)
        return len(buffer)
