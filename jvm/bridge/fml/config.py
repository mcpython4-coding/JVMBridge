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


class ModConfig_Type(NativeClass):
    NAME = "net/minecraftforge/fml/config/ModConfig$Type"

    def __init__(self):
        super().__init__()
        self.exposed_attributes = {
            "COMMON": "common",
            "CLIENT": "client",
            "SERVER": "server",
        }

    @native("extension", "()Ljava/lang/String;")
    def extension(self, instance):
        return instance


class ForgeConfigSpec(NativeClass):
    NAME = "net/minecraftforge/common/ForgeConfigSpec"

    @native("setConfig", "(Lcom/electronwill/nightconfig/core/CommentedConfig;)V")
    def setConfig(self, instance, config_instance):
        pass

    @native("isLoaded", "()Z")
    def isLoaded(self, instance):
        return 1

    @native("save", "()V")
    def save(self, instance):
        pass


class ForgeConfigSpec__BooleanValue(NativeClass):
    NAME = "net/minecraftforge/common/ForgeConfigSpec$BooleanValue"

    @native("get", "()Ljava/lang/Object;")
    def get(self, instance):
        return 0


class ForgeConfigSpec__EnumValue(NativeClass):
    NAME = "net/minecraftforge/common/ForgeConfigSpec$EnumValue"

    @native("set", "(Ljava/lang/Object;)V")
    def set(self, instance, v):
        pass


class ForgeConfigSpec__ConfigValue(NativeClass):
    NAME = "net/minecraftforge/common/ForgeConfigSpec$ConfigValue"

    @native("get", "()Ljava/lang/Object;")
    def get(self, *_):
        pass


class ForgeConfigSpec__IntValue(NativeClass):
    NAME = "net/minecraftforge/common/ForgeConfigSpec$IntValue"

    @native("get", "()Ljava/lang/Object;")
    def get(self, *_):
        return 0


class ForgeConfigSpec__DoubleValue(NativeClass):
    NAME = "net/minecraftforge/common/ForgeConfigSpec$DoubleValue"

    @native("get", "()Ljava/lang/Object;")
    def get(self, *_):
        return 0.0


class ConfigFileTypeHandler(NativeClass):
    NAME = "net/minecraftforge/fml/config/ConfigFileTypeHandler"

    @native("<init>", "()V")
    def init(self, instance):
        pass


class ModConfig(NativeClass):
    NAME = "net/minecraftforge/fml/config/ModConfig"

    @native("<init>",
            "(Lnet/minecraftforge/fml/config/ModConfig$Type;Lnet/minecraftforge/common/ForgeConfigSpec;Lnet/minecraftforge/fml/ModContainer;Ljava/lang/String;)V")
    def init(self, *_):
        pass

    @native("<init>",
            "(Lnet/minecraftforge/fml/config/ModConfig$Type;Lnet/minecraftforge/common/ForgeConfigSpec;Lnet/minecraftforge/fml/ModContainer;)V")
    def init2(self, *_):
        pass


class FMLConfig(NativeClass):
    NAME = "net/minecraftforge/fml/loading/FMLConfig"

    @native("defaultConfigPath", "()Ljava/lang/String;")
    def defaultConfigPath(self, *_):
        return shared.home+"/config"
