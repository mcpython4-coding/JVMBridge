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
import re
import traceback

from mcpython import shared
from mcpython.engine import logger
from jvm.Java import JavaMethod, NativeClass, native


class Pattern(NativeClass):
    NAME = "java/util/regex/Pattern"

    @native("compile", "(Ljava/lang/String;)Ljava/util/regex/Pattern;")
    def compile(self, text: str):
        instance = self.create_instance()
        instance.underlying = re.compile(text)
        return instance

    @native("compile", "(Ljava/lang/String;I)Ljava/util/regex/Pattern;")
    def compile2(self, text: str, v: int):
        instance = self.create_instance()

        try:
            instance.underlying = re.compile(text)
        except re.error:
            logger.print_exception("re.Pattern compilation failed")
            return

        return instance
