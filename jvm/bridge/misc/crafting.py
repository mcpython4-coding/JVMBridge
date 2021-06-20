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


class IRecipeSerializer(NativeClass):
    NAME = "net/minecraft/item/crafting/IRecipeSerializer"


class IRecipeType(NativeClass):
    NAME = "net/minecraft/item/crafting/IRecipeType"

    @native(
        "func_222147_a", "(Ljava/lang/String;)Lnet/minecraft/item/crafting/IRecipeType;"
    )
    def func_222147_a(self, *_):
        return self.create_instance()


class SpecialRecipeSerializer(NativeClass):
    NAME = "net/minecraft/item/crafting/SpecialRecipeSerializer"

    @native("<init>", "(Ljava/util/function/Function;)V")
    def init(self, instance, method):
        pass


class Ingredient(NativeClass):
    NAME = "net/minecraft/item/crafting/Ingredient"

    @native("<init>", "(Ljava/util/stream/Stream;)V")
    def init(self, instance, items):
        instance.items = list(items)


class Ingredient__SingleItemList(NativeClass):
    NAME = "net/minecraft/item/crafting/Ingredient$SingleItemList"

    @native("<init>", "(Lnet/minecraft/item/ItemStack;)V")
    def init(self, instance, itemstack):
        instance.underlying = itemstack


class RecipeManager(NativeClass):
    NAME = "net/minecraft/item/crafting/RecipeManager"

    @native("func_215366_a", "(Lnet/minecraft/item/crafting/IRecipeType;)Ljava/util/Map;")
    def func_215366_a(self, *_):
        pass


class RecipeBookGui(NativeClass):
    NAME = "net/minecraft/client/gui/recipebook/RecipeBookGui"


class RecipeBookPage(NativeClass):
    NAME = "net/minecraft/client/gui/recipebook/RecipeBookPage"
