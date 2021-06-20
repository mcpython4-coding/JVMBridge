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


class GlobalLootModifierSerializer(NativeClass):
    NAME = "net/minecraftforge/common/loot/GlobalLootModifierSerializer"

    @native("<init>", "()V")
    def init(self, instance):
        instance.registry_name = None

    @native(
        "setRegistryName", "(Lnet/minecraft/util/ResourceLocation;)Ljava/lang/Object;"
    )
    def setRegistryName(self, instance, name):
        instance.registry_name = name if isinstance(name, str) else name.name
        return instance

    @native("getRegistryName", "()Lnet/minecraft/util/ResourceLocation;")
    def getRegistryName(self, instance):
        return instance.registry_name

    @native("toString", "()Ljava/lang/String;")
    def toString(self, instance):
        return str(instance)


class ILootSerializer(NativeClass):
    NAME = "net/minecraft/loot/ILootSerializer"


class LootConditionManager(NativeClass):
    NAME = "net/minecraft/loot/conditions/LootConditionManager"

    @native("func_237475_a_",
            "(Ljava/lang/String;Lnet/minecraft/loot/ILootSerializer;)Lnet/minecraft/loot/LootConditionType;")
    def func_237475_a_(self, name: str, serializer):
        pass


class LootConditionType(NativeClass):
    NAME = "net/minecraft/loot/LootConditionType"

    @native("<init>", "(Lnet/minecraft/loot/ILootSerializer;)V")
    def init(self, instance, serializer):
        instance.serializer = serializer


class LootTable(NativeClass):
    NAME = "net/minecraft/loot/LootTable"

