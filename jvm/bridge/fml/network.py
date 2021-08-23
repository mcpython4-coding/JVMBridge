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
from jvm.Java import NativeClass, native


class NetworkRegistry(NativeClass):
    NAME = "net/minecraftforge/fml/network/NetworkRegistry"

    @native(
        "newSimpleChannel",
        "(Lnet/minecraft/util/ResourceLocation;Ljava/util/function/Supplier;Ljava/util/function/Predicate;Ljava/util/function/Predicate;)Lnet/minecraftforge/fml/network/simple/SimpleChannel;",
    )
    def newSimpleChannel(self, namespapce, supplier, predicate1, predicate2):
        return self.vm.get_class(
            "net/minecraftforge/fml/network/simple/SimpleChannel",
            version=self.internal_version,
        ).create_instance()

    @native("newEventChannel",
            "(Lnet/minecraft/util/ResourceLocation;Ljava/util/function/Supplier;Ljava/util/function/Predicate;Ljava/util/function/Predicate;)Lnet/minecraftforge/fml/network/event/EventNetworkChannel;")
    def newEventChannel(self, *_):
        pass


class SimpleChannel(NativeClass):
    NAME = "net/minecraftforge/fml/network/simple/SimpleChannel"

    @native(
        "registerMessage",
        "(ILjava/lang/Class;Ljava/util/function/BiConsumer;Ljava/util/function/Function;Ljava/util/function/BiConsumer;)Lnet/minecraftforge/fml/network/simple/IndexedMessageCodec$MessageHandler;",
    )
    def registerMessage(self, instance, id, cls, consumer_1, function, consumer_2):
        pass


class NetworkRegistry__ChannelBuilder(NativeClass):
    NAME = "net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder"

    @native(
        "named",
        "(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder;",
    )
    def named(self, name):
        return self.create_instance()

    @native(
        "clientAcceptedVersions",
        "(Ljava/util/function/Predicate;)Lnet/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder;",
    )
    def clientAcceptedVersions(self, instance, predicate):
        return instance

    @native(
        "serverAcceptedVersions",
        "(Ljava/util/function/Predicate;)Lnet/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder;",
    )
    def serverAcceptedVersions(self, instance, predicate):
        return instance

    @native(
        "networkProtocolVersion",
        "(Ljava/util/function/Supplier;)Lnet/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder;",
    )
    def networkProtocolVersion(self, instance, supplier):
        return instance

    @native("simpleChannel", "()Lnet/minecraftforge/fml/network/simple/SimpleChannel;")
    def simpleChannel(self, instance):
        return self.vm.get_class(
            "net/minecraftforge/fml/network/simple/SimpleChannel",
            version=self.internal_version,
        )

    @native(
        "eventNetworkChannel",
        "()Lnet/minecraftforge/fml/network/event/EventNetworkChannel;",
    )
    def eventNetworkChannel(self, instance):
        return self.vm.get_class(
            "net/minecraftforge/fml/event/EventNetworkChannel",
            version=self.internal_version,
        )


class EventNetworkChannel(NativeClass):
    NAME = "net/minecraftforge/fml/network/event/EventNetworkChannel"

    @native("registerObject", "(Ljava/lang/Object;)V")
    def registerObject(self, instance, obj):
        pass


class DataSerializers(NativeClass):
    NAME = "net/minecraft/network/datasync/DataSerializers"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "field_187197_g": None,
            "field_187192_b": None,
            "field_187193_c": None,
            "field_187200_j": None,
            "field_187196_f": None,
            "field_187198_h": None,
            "field_187191_a": None,
            "field_192734_n": None,
            "field_187203_m": None,
            "field_187202_l": None,
        })

    @native("func_187189_a", "(Lnet/minecraft/network/datasync/IDataSerializer;)V")
    def func_187189_a(self, *_):
        pass


class EntityDataManager(NativeClass):
    NAME = "net/minecraft/network/datasync/EntityDataManager"

    @native("func_187226_a",
            "(Ljava/lang/Class;Lnet/minecraft/network/datasync/IDataSerializer;)Lnet/minecraft/network/datasync/DataParameter;")
    def func_187226_a(self, *_):
        pass


class ServerPlayNetHandler(NativeClass):
    NAME = "net/minecraft/network/play/ServerPlayNetHandler"


class NettyCompressionDecoder(NativeClass):
    NAME = "net/minecraft/network/NettyCompressionDecoder"


class PacketBuffer(NativeClass):
    NAME = "net/minecraft/network/PacketBuffer"


class ServerLoginNetHandler(NativeClass):
    NAME = "net/minecraft/network/login/ServerLoginNetHandler"
