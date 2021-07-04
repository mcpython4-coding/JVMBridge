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


class Method(NativeClass):
    NAME = "java/lang/reflect/Method"

    @native("init", "()V")
    def init(self, *_):
        pass

    @native("getClass", "()Ljava/lang/Class;")
    def getClass(self, instance):
        return self

    @native("accept", "(Ljava/lang/Object;)V")
    def accept(self, instance, obj):
        instance(obj)

    @native("apply", "(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;")
    def apply(self, instance, arg1, arg2):
        return instance(arg1, arg2)

    @native("apply", "(Ljava/lang/Object;)Ljava/lang/Object;")
    def apply2(self, instance, arg):
        return instance(arg)

    @native("accept", "(Ljava/lang/Object;)V")
    def accept(self, instance, arg):
        return instance(arg)

    @native("accept", "(Ljava/lang/Object;Ljava/lang/Object;)V")
    def accept2(self, instance, arg1, arg2):
        return instance(arg1, arg2)

    @native("get", "()Ljava/lang/Object;")
    def get(self, instance):
        return instance()

    @native("getAnnotation", "(Ljava/lang/Class;)Ljava/lang/annotation/Annotation;")
    def getAnnotation(self, *_):
        pass

    @native("run", "()V")
    def run(self, instance):
        instance()

    @native("setAccessible", "(Z)V")
    def setAccessible(self, *_):
        pass

    @native("accept",
            "(Ljava/lang/String;Ljava/lang/Class;Lcom/simibubi/create/repack/registrate/builders/Builder;Lcom/simibubi/create/repack/registrate/util/nullness/NonNullSupplier;Lcom/simibubi/create/repack/registrate/util/nullness/NonNullFunction;)Lcom/simibubi/create/repack/registrate/util/entry/RegistryEntry;")
    def special_accept(self, instance, *args):
        return instance(*args)

    @native("invoke", "(Ljava/lang/Object;[Ljava/lang/Object;)Ljava/lang/Object;")
    def special_invoke(self, instance, *args):
        instance(*args)

    @native("get", "(Ljava/lang/Enum;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def special_get(self, instance, *args):
        return instance(*args)
