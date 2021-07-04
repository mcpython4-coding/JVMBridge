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
import math

from mcpython import shared
from jvm.Java import NativeClass, native


class Math(NativeClass):
    NAME = "java/lang/Math"

    @native("max", "(DD)D")
    def max(self, a, b):
        return max(a, b)

    @native("max", "(FF)F")
    def max2(self, a, b):
        return max(a, b)

    @native("max", "(JJ)J")
    def max3(self, a, b):
        return max(a, b)

    @native("max", "(II)I")
    def max4(self, a, b):
        return max(a, b)

    @native("min", "(DD)D")
    def min(self, a, b):
        return min(a, b)

    @native("min", "(FF)F")
    def min2(self, a, b):
        return min(a, b)

    @native("min", "(JJ)J")
    def min3(self, a, b):
        return min(a, b)

    @native("min", "(II)I")
    def min4(self, a, b):
        return min(a, b)

    @native("pow", "(DD)D")
    def pow(self, a, b):
        return a ** b

    @native("round", "(D)J")
    def round(self, instance):
        return round(instance)

    @native("log10", "(D)D")
    def log10(self, value):
        return math.log10(value)
