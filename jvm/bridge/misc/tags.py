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


class BlockTags(NativeClass):
    NAME = "net/minecraft/tags/BlockTags"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "field_203292_x": None,
            "field_203291_w": None,
            "field_219757_z": None,
            "field_199898_b": None,
            "field_219748_G": None,
            "field_232868_aA_": None,
            "field_212185_E": None,
            "field_200029_f": None,
        })

    @native("func_199894_a", "(Ljava/lang/String;)Lnet/minecraft/tags/ITag$INamedTag;")
    def getByName(self, name: str):
        return shared.tag_handler.get_tag_for(name, "blocks", or_else_none=True)

    @native(
        "createOptional",
        "(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/common/Tags$IOptionalNamedTag;",
    )
    def createOptional(self, name: str):
        pass

    @native("func_242174_b", "()Ljava/util/List;")
    def func_242174_b(self, *_):
        return []


class ItemTags(NativeClass):
    NAME = "net/minecraft/tags/ItemTags"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "field_203442_w": None,
            "field_203441_v": None,
            "field_219778_z": None,
            "field_199905_b": None,
            "field_219772_G": None,
            "field_212187_B": None,
            "field_200036_f": None,
        })

    @native("func_199901_a", "(Ljava/lang/String;)Lnet/minecraft/tags/ITag$INamedTag;")
    def func_199901_a(self, name: str):
        return shared.tag_handler.get_tag_for(name, "items", or_else_none=True)

    @native(
        "createOptional",
        "(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/common/Tags$IOptionalNamedTag;",
    )
    def createOptional(self, name: str):
        pass


class FluidTags(NativeClass):
    NAME = "net/minecraft/tags/FluidTags"

    @native(
        "createOptional",
        "(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/common/Tags$IOptionalNamedTag;",
    )
    def createOptional(self, *_):
        pass

    @native("func_206956_a", "(Ljava/lang/String;)Lnet/minecraft/tags/ITag$INamedTag;")
    def func_206956_a(self, *_):
        pass


class EntityTypeTags(NativeClass):
    NAME = "net/minecraft/tags/EntityTypeTags"

    @native("createOptional",
            "(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/common/Tags$IOptionalNamedTag;")
    def createOptional(self, *_):
        pass

    @native("func_232896_a_", "(Ljava/lang/String;)Lnet/minecraft/tags/ITag$INamedTag;")
    def func_232896_a_(self, *_):
        pass


class ForgeTagHandler(NativeClass):
    NAME = "net/minecraftforge/common/ForgeTagHandler"

    @native(
        "createOptionalTag",
        "(Lnet/minecraftforge/registries/IForgeRegistry;Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/common/Tags$IOptionalNamedTag;",
    )
    def createOptionalTag(self, registry, name):
        pass
