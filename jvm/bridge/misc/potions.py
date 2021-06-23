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


class Effects(NativeClass):
    NAME = "net/minecraft/potion/Effects"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_76424_c": None,
                "field_76431_k": None,
                "field_180152_w": None,
                "field_76438_s": None,
                "field_76444_x": None,
                "field_76441_p": None,
                "field_76428_l": None,
                "field_188423_x": None,
                "field_189112_A": None,
                "field_76426_n": None,
                "field_76419_f": None,
                "field_76430_j": None,
                "field_76436_u": None,
                "field_76429_m": None,
                "field_76437_t": None,
                "field_76427_o": None,
                "field_76439_r": None,
                "field_82731_v": None,
                "field_76420_g": None,
                "field_76440_q": None,
                "field_76443_y": None,
                "field_76422_e": None,
                "field_76432_h": None,
                "field_76421_d": None,
                "field_188425_z": None,
                "field_204839_B": None,
                "field_188424_y": None,
                "field_76433_i": None,
            }
        )

    @native("func_76403_b", "()Z")
    def func_76403_b(self, instance) -> bool:
        return False


class Effect(NativeClass):
    NAME = "net/minecraft/potion/Effect"

    @native("func_76403_b", "()Z")
    def func_76403_b(self, instance):
        return False

    @native("<init>", "(Lnet/minecraft/potion/EffectType;I)V")
    def init(self, *_):
        pass


class Potion(NativeClass):
    NAME = "net/minecraft/potion/Potion"


class EffectType(NativeClass):
    NAME = "net/minecraft/potion/EffectType"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "NEUTRAL": 0,
                "HARMFUL": 1,
                "BENEFICIAL": 2,
            }
        )


class InstantEffect(NativeClass):
    NAME = "net/minecraft/potion/InstantEffect"

    @native("<init>", "(Lnet/minecraft/potion/EffectType;I)V")
    def init(self, instance, effect_type, v):
        pass


class Potions(NativeClass):
    NAME = "net/minecraft/potion/Potions"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "field_185230_b": None,
            "field_185233_e": None,
        })


class PotionUtils(NativeClass):
    NAME = "net/minecraft/potion/PotionUtils"

    @native("func_185188_a",
            "(Lnet/minecraft/item/ItemStack;Lnet/minecraft/potion/Potion;)Lnet/minecraft/item/ItemStack;")
    def func_185188_a(self, itemstack, potion):
        return itemstack

    @native("func_185181_a", "(Ljava/util/Collection;)I")
    def func_185181_a(self, *_):
        return []


class EffectInstance(NativeClass):
    NAME = "net/minecraft/potion/EffectInstance"

    @native("<init>", "(Lnet/minecraft/potion/Effect;II)V")
    def init(self, instance, effect, a, b):
        pass


class PotionBrewing(NativeClass):
    NAME = "net/minecraft/potion/PotionBrewing"
