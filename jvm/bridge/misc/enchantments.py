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


class EnchantmentType(NativeClass):
    NAME = "net/minecraft/enchantment/EnchantmentType"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "ARMOR": 0,
            "ARMOR_FEET": 1,
            "ARMOR_LEGS": 2,
            "ARMOR_CHEST": 3,
            "ARMOR_HEAD": 4,
            "WEAPON": 5,
            "DIGGER": 6,
            "FISHING_ROD": 7,
            "TRIDENT": 8,
            "BREAKABLE": 9,
            "BOW": 10,
            "WEARABLE": 11,
            "CROSSBOW": 12,
            "VANISHABLE": 13,
        })

    @native(
        "create",
        "(Ljava/lang/String;Ljava/util/function/Predicate;)Lnet/minecraft/enchantment/EnchantmentType;",
    )
    def create(self, *_):
        return self.create_instance()


class Enchantment(NativeClass):
    NAME = "net/minecraft/enchantment/Enchantment"


class EnchantmentHelper(NativeClass):
    NAME = "net/minecraft/enchantment/EnchantmentHelper"


class Enchantments(NativeClass):
    NAME = "net/minecraft/enchantment/Enchantments"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "field_180310_c": 0,
            "field_185297_d": 1,
            "field_180309_e": 2,
            "field_77329_d": 3,
            "field_180308_g": 4,
            "field_77334_n": 5,
            "field_185301_j": 6,
            "field_180313_o": 7,
            "field_185304_p": 8,
            "field_92091_k": 9,
            "field_185296_A": 10,
        })
