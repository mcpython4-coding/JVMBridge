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
import traceback

import mcpython.common.mod.ModLoader
import mcpython.common.mod.util
from mcpython import shared
from mcpython.engine import logger
from jvm.Java import NativeClass, native
from jvm.JavaExceptionStack import StackCollectingException
from jvm.Runtime import Runtime


NAME2STAGE = {
    (
        "registerBlocks",
        "(Lnet/minecraftforge/event/RegistryEvent$Register;)V",
    ): ("stage:block:factory_usage", lambda: shared.registry.get_by_name("minecraft:block")),
    (
        "registerItems",
        "(Lnet/minecraftforge/event/RegistryEvent$Register;)V",
    ): ("stage:item:factory_usage", shared.registry.get_by_name("minecraft:item")),
    (
        'init',
        '(Ljava/lang/Object;)V'
    ): ("stage:mod:init", None),
    ('preInit', '(Ljava/lang/Object;)V'): ("stage:mod:init", None),
    ('registerCommands', '(Ljava/lang/Object;)V'): ("stage:commands", None),
    ('commonSetup', '(Ljava/lang/Object;)V'): ("stage:mod:init", None),
    (
        "preInit",
        "(Lnet/minecraftforge/fml/event/lifecycle/FMLCommonSetupEvent;)V",
    ): ("stage:mod:init", None),
    ('configEvent', '(Lnet/minecraftforge/fml/config/ModConfig$ModConfigEvent;)V'): ("stage:mod:config:load", None),
    ('updateLocatable', '(Ljava/lang/Object;)V'): ("stage:language", None),
    ('registerDimension', '(Ljava/lang/Object;)V'): ("stage:dimension", None),
    ('addWorldGenToBiome', '(Ljava/lang/Object;)V'): ("stage:worldgen:biomes", None),
    ('setupCommon', '(Ljava/lang/Object;)V'): ("stage:mod:init", None),
    ('setup', '(Ljava/lang/Object;)V'): ("stage:mod:init", None),
    ('onLoadComplete', '(Ljava/lang/Object;)V'): ("stage:post", None),
    ('onModloadingComplete', '(Ljava/lang/Object;)V'): ("stage:post", None),
    ('onCommonSetup', '(Ljava/lang/Object;)V'): ("stage:mod:init", None),
    ('common', '(Ljava/lang/Object;)V'): ("stage:mod:init", None),
}


if shared.IS_CLIENT:
    NAME2STAGE.update({
        ('clientSetup', '(Ljava/lang/Object;)V'): ("stage:mod:init", None),
        (
            "setupClient",
            "(Lnet/minecraftforge/fml/event/lifecycle/FMLClientSetupEvent;)V",
        ): ("stage:mod:init", None),
        ('client', '(Ljava/lang/Object;)V'): ("stage:mod:init", None),
        ('preInitClient', '(Ljava/lang/Object;)V'): ("stage:mod:init", None),
        ('setupClient', '(Ljava/lang/Object;)V'): ("stage:mod:init", None),
    })


class Minecraft(NativeClass):
    NAME = "net/minecraft/client/Minecraft"

    def __init__(self):
        super().__init__()
        self.instance = self.create_instance()

    @native("func_71410_x", "()Lnet/minecraft/client/Minecraft;", static=True)
    def func_71410_x(self):
        return self.instance

    @native("func_184125_al", "()Lnet/minecraft/client/renderer/color/BlockColors;")
    def func_184125_al(self, instance):
        pass

    def get_dynamic_field_keys(self):
        return {"field_71412_D"}


class Mod(NativeClass):
    NAME = "net/minecraftforge/fml/common/Mod"

    def on_annotate(self, cls, args):
        import jvm.Runtime

        runtime = jvm.Runtime.Runtime()
        instance = cls.create_instance()
        runtime.run_method(cls.get_method("<init>", "()V"), instance)


class Mod_EventBusSubscriber(NativeClass):
    NAME = "net/minecraftforge/fml/common/Mod$EventBusSubscriber"

    def on_annotate(self, cls, args):

        for signature, (stage, arg_getter) in NAME2STAGE.items():
            if signature in cls.methods:
                current_mod = shared.CURRENT_EVENT_SUB

                @shared.mod_loader(current_mod, stage)
                def load():
                    shared.CURRENT_EVENT_SUB = current_mod

                    try:
                        method = cls.get_method(*signature)
                    except StackCollectingException as e:
                        e.add_trace(cls).add_trace(signature)

                        logger.print_exception(f"during annotation processing class {cls}")
                        print(e.format_exception())

                        from mcpython.common.mod.util import LoadingInterruptException
                        raise LoadingInterruptException from None

                    runtime = Runtime()

                    try:
                        runtime.run_method(
                            method, *(arg_getter() if arg_getter is not None else tuple())
                        )
                    except StackCollectingException as e:
                        import mcpython.client.state.LoadingExceptionViewState

                        traceback.print_exc()
                        mcpython.client.state.LoadingExceptionViewState.error_occur(
                            e.format_exception()
                        )
                        print(e.format_exception())
                        raise mcpython.common.mod.util.LoadingInterruptException from None

                    except:
                        import mcpython.client.state.LoadingExceptionViewState

                        mcpython.client.state.LoadingExceptionViewState.error_occur(
                            traceback.format_exc()
                        )
                        traceback.print_exc()
                        raise mcpython.common.mod.util.LoadingInterruptException from None


class Mod_EventBusSubscriber_Bus(NativeClass):
    NAME = "net/minecraftforge/fml/common/Mod$EventBusSubscriber$Bus"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "MOD": "net/minecraftforge/fml/common/Mod$EventBusSubscriber$Bus::MOD",
                "FORGE": "net/minecraftforge/fml/common/Mod$EventBusSubscriber$Bus::FORGE",
            }
        )

    @native("bus", "()Ljava/util/function/Supplier;")
    def bus(self, instance):
        return lambda: None


class FMLLoadingContext(NativeClass):
    NAME = "net/minecraftforge/fml/javafmlmod/FMLJavaModLoadingContext"

    @native("get", "()Lnet/minecraftforge/fml/javafmlmod/FMLJavaModLoadingContext;")
    def get_context(self):
        pass

    @native("getModEventBus", "()Lnet/minecraftforge/eventbus/api/IEventBus;")
    def getModEventBus(self, instance):
        pass


class ModLoadingContext(NativeClass):
    NAME = "net/minecraftforge/fml/ModLoadingContext"

    @native("get", "()Lnet/minecraftforge/fml/ModLoadingContext;")
    def get_context(self):
        pass

    @native(
        "registerConfig",
        "(Lnet/minecraftforge/fml/config/ModConfig$Type;Lnet/minecraftforge/common/ForgeConfigSpec;Ljava/lang/String;)V",
    )
    def registerConfig(self, instance, config_type, config_spec, file_name: str):
        pass

    @native(
        "registerConfig",
        "(Lnet/minecraftforge/fml/config/ModConfig$Type;Lnet/minecraftforge/common/ForgeConfigSpec;)V",
    )
    def registerConfig2(self, instance, config_type, config_spec):
        pass

    @native(
        "registerExtensionPoint",
        "(Lnet/minecraftforge/fml/ExtensionPoint;Ljava/util/function/Supplier;)V",
    )
    def registerExtensionPoint(self, instance, point, supplier):
        pass

    @native("getActiveContainer", "()Lnet/minecraftforge/fml/ModContainer;")
    def getActiveContainer(self, instance):
        return shared.mod_loader[shared.CURRENT_EVENT_SUB]


class ModContainer(NativeClass):
    NAME = "net/minecraftforge/fml/ModContainer"

    @native("getModId", "()Ljava/lang/String;")
    def getModId(self, instance):
        return instance.name

    @native("addConfig", "(Lnet/minecraftforge/fml/config/ModConfig;)V")
    def addConfig(self, *_):
        pass

    @native("getModInfo", "()Lnet/minecraftforge/forgespi/language/IModInfo;")
    def getModInfo(self, instance):
        return instance


class IModInfo(NativeClass):
    NAME = "net/minecraftforge/forgespi/language/IModInfo"

    @native("getVersion", "()Lorg/apache/maven/artifact/versioning/ArtifactVersion;")
    def getVersion(self, instance):
        return instance.version


class EventBus(NativeClass):
    NAME = "net/minecraftforge/eventbus/api/IEventBus"

    @native("addListener", "(Ljava/util/function/Consumer;)V")
    def addListener(self, instance, function):
        if not callable(function):
            logger.println(f"[FML][WARN] tried to add listener {function} which seems to be non!")
            return

        func_name = function.name if hasattr(function, "name") else function.native_name
        func_signature = function.signature if hasattr(function, "signature") else function.native_signarure

        if (func_name, func_signature) in NAME2STAGE:
            current_mod = shared.CURRENT_EVENT_SUB
            stage, arg_getter = NAME2STAGE[(func_name, func_signature)]

            @shared.mod_loader(current_mod, "stage:block:factory_usage")
            def load():
                shared.CURRENT_EVENT_SUB = current_mod
                method = function.class_file.get_method(*func_signature)

                runtime = Runtime()

                try:
                    runtime.run_method(
                        method, *(arg_getter() if arg_getter is not None else tuple())
                    )
                except StackCollectingException as e:
                    import mcpython.client.state.LoadingExceptionViewState

                    traceback.print_exc()
                    mcpython.client.state.LoadingExceptionViewState.error_occur(
                        e.format_exception()
                    )
                    print(e.format_exception())
                    raise mcpython.common.mod.util.LoadingInterruptException from None

                except:
                    import mcpython.client.state.LoadingExceptionViewState

                    mcpython.client.state.LoadingExceptionViewState.error_occur(
                        traceback.format_exc()
                    )
                    traceback.print_exc()
                    raise mcpython.common.mod.util.LoadingInterruptException from None
        else:
            print("missing BRIDGE binding for", function, (function.name, function.signature))

    @native(
        "addListener",
        "(Lnet/minecraftforge/eventbus/api/EventPriority;Ljava/util/function/Consumer;)V",
    )
    def addListener2(self, instance, priority, consumer):
        self.addListener(priority, consumer)

    @native("addListener",
            "(Lnet/minecraftforge/eventbus/api/EventPriority;ZLjava/lang/Class;Ljava/util/function/Consumer;)V")
    def addListener3(self, instance, priority, v, cls, consumer):
        self.addListener(priority, consumer)

    @native("register", "(Ljava/lang/Object;)V")
    def register(self, instance, obj):
        pass  # todo: do something here

    @native("addGenericListener", "(Ljava/lang/Class;Ljava/util/function/Consumer;)V")
    def addGenericListener(self, instance, cls, consumer):
        return
        # todo: implement
        current_mod = shared.CURRENT_EVENT_SUB
        if cls.name == "net/minecraft/block/Block":

            @shared.mod_loader("minecraft", "stage:block:factory_usage")
            def load():
                shared.CURRENT_EVENT_SUB = current_mod

                runtime = Runtime()

                try:
                    runtime.run_method(
                        consumer, shared.registry.get_by_name("minecraft:block")
                    )
                except StackCollectingException as e:
                    import mcpython.client.state.LoadingExceptionViewState

                    mcpython.client.state.LoadingExceptionViewState.error_occur(
                        e.format_exception()
                    )
                    logger.write_into_container(e.format_exception())
                    raise mcpython.common.mod.util.LoadingInterruptException from None
                except:
                    import mcpython.client.state.LoadingExceptionViewState

                    mcpython.client.state.LoadingExceptionViewState.error_occur(
                        traceback.format_exc()
                    )
                    traceback.print_exc()
                    raise mcpython.common.mod.util.LoadingInterruptException from None

    @native(
        "addGenericListener",
        "(Ljava/lang/Class;Lnet/minecraftforge/eventbus/api/EventPriority;ZLjava/lang/Class;Ljava/util/function/Consumer;)V",
    )
    def addGenericListener2(self, instance, cls, priority, b, cls2, consumer):
        # todo: use priority stuff
        self.addGenericListener(instance, cls, consumer)

    @native("post", "(Lnet/minecraftforge/eventbus/api/Event;)Z")
    def post(self, instance, event):
        pass  # todo: add translation system

    @native("addGenericListener",
            "(Ljava/lang/Class;Lnet/minecraftforge/eventbus/api/EventPriority;Ljava/util/function/Consumer;)V")
    def addGenericListener3(self, instance, cls, priority, consumer):
        # todo: use priority stuff
        self.addGenericListener(instance, cls, consumer)


class EventBus2(EventBus):
    NAME = "net/minecraftforge/eventbus/EventBus"


class Dist(NativeClass):
    NAME = "net/minecraftforge/api/distmarker/Dist"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "CLIENT": "client",
                "SERVER": "server",
                "DEDICATED_SERVER": "dedicated_server",
            }
        )
        self.keys = list(self.exposed_attributes.keys())

    @native("isClient", "()Z")
    def isClient(self, instance):
        return int(instance == "client")

    @native("values", "()[Lnet/minecraftforge/api/distmarker/Dist;")
    def values(self, *_):
        return list(self.exposed_attributes.values())

    @native("ordinal", "()I")
    def ordinal(self, value):
        for i, key in enumerate(self.keys):
            if self.exposed_attributes[key] == value:
                return i

        return -1


class FMLEnvironment(NativeClass):
    NAME = "net/minecraftforge/fml/loading/FMLEnvironment"

    def __init__(self):
        super().__init__()
        self.exposed_attributes["dist"] = "client" if shared.IS_CLIENT else "server"
        self.exposed_attributes["production"] = 1


class DistExecutor(NativeClass):
    NAME = "net/minecraftforge/fml/DistExecutor"

    @native(
        "runForDist",
        "(Ljava/util/function/Supplier;Ljava/util/function/Supplier;)Ljava/lang/Object;",
    )
    def runForDist(self, left, right):
        if shared.IS_CLIENT:
            return left()
        return right()

    @native(
        "unsafeRunForDist",
        "(Ljava/util/function/Supplier;Ljava/util/function/Supplier;)Ljava/lang/Object;",
    )
    def unsafeRunForDist(self, left, right):
        return self.runForDist(left, right)

    @native(
        "unsafeCallWhenOn",
        "(Lnet/minecraftforge/api/distmarker/Dist;Ljava/util/function/Supplier;)Ljava/lang/Object;",
    )
    def unsafeCallWhenOn(self, dist, supplier):
        if dist != "client" or shared.IS_CLIENT:
            supplier()

    @native(
        "runWhenOn",
        "(Lnet/minecraftforge/api/distmarker/Dist;Ljava/util/function/Supplier;)V",
    )
    def runWhenOn(self, dist, supplier):
        self.unsafeCallWhenOn(dist, supplier)

    @native(
        "unsafeRunWhenOn",
        "(Lnet/minecraftforge/api/distmarker/Dist;Ljava/util/function/Supplier;)V",
    )
    def unsafeRunWhenOn(self, dist, supplier):
        self.unsafeCallWhenOn(dist, supplier)

    @native(
        "callWhenOn",
        "(Lnet/minecraftforge/api/distmarker/Dist;Ljava/util/function/Supplier;)Ljava/lang/Object;",
    )
    def callWhenOn(self, dist, supplier):
        self.unsafeCallWhenOn(dist, supplier)

    @native(
        "safeRunWhenOn",
        "(Lnet/minecraftforge/api/distmarker/Dist;Ljava/util/function/Supplier;)V",
    )
    def safeRunWhenOn(self, dist, supplier):
        self.unsafeCallWhenOn(dist, supplier)

    @native(
        "safeRunForDist",
        "(Ljava/util/function/Supplier;Ljava/util/function/Supplier;)Ljava/lang/Object;",
    )
    def safeRunForDist(self, dist, supplier):
        self.unsafeCallWhenOn(dist, supplier)


class FMLPaths(NativeClass):
    NAME = "net/minecraftforge/fml/loading/FMLPaths"

    def __init__(self):
        super().__init__()
        config_dir = self.create_instance()
        config_dir.dir = shared.home + "/fml_configs"

        game_dir = self.create_instance()
        game_dir.dir = shared.home

        self.exposed_attributes = {"CONFIGDIR": config_dir, "GAMEDIR": game_dir}

    @native("get", "()Ljava/nio/file/Path;")
    def get(self, instance):
        obj = self.vm.get_class("java/io/Path", version=self.internal_version)
        obj.path = instance.dir
        return obj

    @native(
        "getOrCreateGameRelativePath",
        "(Ljava/nio/file/Path;Ljava/lang/String;)Ljava/nio/file/Path;",
    )
    def getOrCreateGameRelativePath(self, path, sub):
        return path  # todo: implement


class ForgeConfigSpec__Builder(NativeClass):
    NAME = "net/minecraftforge/common/ForgeConfigSpec$Builder"

    @native("<init>", "()V")
    def init(self, instance):
        pass

    @native(
        "comment",
        "(Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;",
    )
    def comment(self, instance, text: str):
        return instance

    @native(
        "push",
        "(Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;",
    )
    def push(self, instance, text: str):
        return instance

    @native(
        "defineEnum",
        "(Ljava/lang/String;Ljava/lang/Enum;)Lnet/minecraftforge/common/ForgeConfigSpec$EnumValue;",
    )
    def defineEnum(self, instance, name: str, enum):
        return instance

    @native("defineEnum", "(Ljava/lang/String;Ljava/lang/Enum;)Lnet/minecraftforge/common/ForgeConfigSpec$EnumValue;")
    def defineEnum3(self, instance, *_):
        return instance

    @native(
        "defineEnum",
        "(Ljava/lang/String;Ljava/lang/Enum;[Ljava/lang/Enum;)Lnet/minecraftforge/common/ForgeConfigSpec$EnumValue;",
    )
    def defineEnum2(self, instance, name: str, enum, values):
        pass

    @native("defineEnum",
            "(Ljava/lang/String;Ljava/lang/Enum;Lcom/electronwill/nightconfig/core/EnumGetMethod;)Lnet/minecraftforge/common/ForgeConfigSpec$EnumValue;")
    def defineEnum4(self, *_):
        pass

    @native(
        "define",
        "(Ljava/lang/String;Z)Lnet/minecraftforge/common/ForgeConfigSpec$BooleanValue;",
    )
    def defineBool(self, instance, name: str, default: bool):
        return instance

    @native("pop", "()Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    def pop(self, instance):
        return instance

    @native("build", "()Lnet/minecraftforge/common/ForgeConfigSpec;")
    def build(self, instance):
        return self.vm.get_class(
            "net/minecraftforge/common/ForgeConfigSpec"
        ).create_instance()

    @native(
        "configure",
        "(Ljava/util/function/Function;)Lorg/apache/commons/lang3/tuple/Pair;",
    )
    def configure(self, instance, function):
        o = function(instance)
        return o, self.build(instance)

    @native(
        "comment",
        "([Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;",
    )
    def comment(self, instance, comments):
        return instance

    @native(
        "comment",
        "(Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;",
    )
    def comment2(self, instance, comments):
        return instance

    @native(
        "define",
        "(Ljava/lang/String;Ljava/lang/Object;)Lnet/minecraftforge/common/ForgeConfigSpec$ConfigValue;",
    )
    def define(self, instance, name, obj):
        return instance

    @native("define",
            "(Ljava/lang/String;Ljava/lang/Object;Ljava/util/function/Predicate;)Lnet/minecraftforge/common/ForgeConfigSpec$ConfigValue;")
    def define2(self, instance, *_):
        return instance

    @native(
        "defineInRange",
        "(Ljava/lang/String;III)Lnet/minecraftforge/common/ForgeConfigSpec$IntValue;",
    )
    def defineInRange(self, instance, name, a, b, c):
        return instance

    @native(
        "defineInRange",
        "(Ljava/lang/String;DDD)Lnet/minecraftforge/common/ForgeConfigSpec$DoubleValue;",
    )
    def defineInRange2(self, instance, name: str, a, b, c):
        pass

    @native("defineInRange", "(Ljava/lang/String;JJJ)Lnet/minecraftforge/common/ForgeConfigSpec$LongValue;")
    def defineInRange3(self, *_):
        pass

    @native(
        "defineList",
        "(Ljava/lang/String;Ljava/util/List;Ljava/util/function/Predicate;)Lnet/minecraftforge/common/ForgeConfigSpec$ConfigValue;",
    )
    def defineList(self, instance, name, a, b):
        return instance

    @native("defineList",
            "(Ljava/lang/String;Ljava/util/function/Supplier;Ljava/util/function/Predicate;)Lnet/minecraftforge/common/ForgeConfigSpec$ConfigValue;")
    def defineList2(self, *_):
        pass

    @native(
        "translation",
        "(Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;",
    )
    def translation(self, instance, key: str):
        pass

    @native("worldRestart", "()Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    def worldRestart(self, *_):
        pass

    @native("get", "()Ljava/lang/Object;")
    def get(self, instance):
        pass

    @native("pop", "(I)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    def pop(self, instance, count: int):
        return instance

    @native("pop", "()Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    def pop2(self, instance):
        return instance

    @native("push", "(Ljava/util/List;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    def push(self, instance, array):
        return instance

    @native("push", "(Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    def push(self, instance, text):
        return instance


class FMLCommonSetupEvent(NativeClass):
    NAME = "net/minecraftforge/fml/event/lifecycle/FMLCommonSetupEvent"

    @native(
        "enqueueWork", "(Ljava/lang/Runnable;)Ljava/util/concurrent/CompletableFuture;"
    )
    def enqueueWork(self, instance, work):
        work(None)


class OnlyIn(NativeClass):
    NAME = "net/minecraftforge/api/distmarker/OnlyIn"

    def on_annotate(self, cls, args):
        return
        # logger.println(
        #     f"[FML][WARN] got internal @OnlyIn marker on cls {cls.name} not specified for use in mods. Things may break!"
        # )


class MinecraftForge(NativeClass):
    NAME = "net/minecraftforge/common/MinecraftForge"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "EVENT_BUS": None,
            }
        )


class ModList(NativeClass):
    NAME = "net/minecraftforge/fml/ModList"

    @native("get", "()Lnet/minecraftforge/fml/ModList;")
    def getModList(self):
        return self

    @native("isLoaded", "(Ljava/lang/String;)Z")
    def isLoaded(self, instance, name: str):
        return int(name in shared.mod_loader.mods)

    @native(
        "getModFileById",
        "(Ljava/lang/String;)Lnet/minecraftforge/fml/loading/moddiscovery/ModFileInfo;",
    )
    def getModFileById(self, instance, name: str):
        return shared.mod_loader.mods[name]

    @native("getModContainerById", "(Ljava/lang/String;)Ljava/util/Optional;")
    def getModContainerById(self, instance, name: str):
        return shared.mod_loader.mods[name] if name in shared.mod_loader.mods else None

    @native("getAllScanData", "()Ljava/util/List;")
    def getAllScanData(self, *_):
        return []

    @native("getMods", "()Ljava/util/List;")
    def getMods(self, *_):
        return list(shared.mod_loader.mods.values())


class ModFileInfo(NativeClass):
    NAME = "net/minecraftforge/fml/loading/moddiscovery/ModFileInfo"

    @native("getFile", "()Lnet/minecraftforge/fml/loading/moddiscovery/ModFile;")
    def getFile(self, instance):
        return instance.path


class ModFile(NativeClass):
    NAME = "net/minecraftforge/fml/loading/moddiscovery/ModFile"

    @native("getScanResult", "()Lnet/minecraftforge/forgespi/language/ModFileScanData;")
    def getScanResult(self, instance):
        pass


class ModFileScanData(NativeClass):
    NAME = "net/minecraftforge/forgespi/language/ModFileScanData"

    @native("getAnnotations", "()Ljava/util/Set;")
    def getAnnotations(self, instance):
        return set()


class Event(NativeClass):
    NAME = "net/minecraftforge/eventbus/api/Event"

    @native("<init>", "()V")
    def init(self, instance):
        pass


class Event__HasResult(NativeClass):
    NAME = "net/minecraftforge/eventbus/api/Event$HasResult"


class EventPriority(NativeClass):
    NAME = "net/minecraftforge/eventbus/api/EventPriority"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "HIGHEST": 0,
                "HIGH": 1,
                "NORMAL": 2,
                "LOW": 3,
                "LOWEST": 4,
            }
        )


class IEnvironment__Keys(NativeClass):
    NAME = "cpw/mods/modlauncher/api/IEnvironment$Keys"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({"VERSION": self.get_version, "NAMING": lambda: None})

    @native("<get_version>", "()Ljava/lang/Object;")
    def get_version(self):
        return 1


class Environment(NativeClass):
    NAME = "cpw/mods/modlauncher/Environment"

    def __init__(self):
        super().__init__()
        self.map = {}

    @native("getProperty", "(Lcpw/mods/modlauncher/api/TypesafeMap$Key;)Ljava/util/Optional;")
    def getProperty(self, instance, key):
        return None if key not in self.map else self.map[key]


class Launcher(NativeClass):
    NAME = "cpw/mods/modlauncher/Launcher"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({"INSTANCE": self.create_instance()})
        self.environment = Environment()

    @native("environment", "()Lcpw/mods/modlauncher/Environment;")
    def environment(self, *_):
        return self.environment


class Cancelable(NativeClass):
    NAME = "net/minecraftforge/eventbus/api/Cancelable"

    def on_annotate(self, cls, args):
        pass


class ObfuscationReflectionHelper(NativeClass):
    NAME = "net/minecraftforge/fml/common/ObfuscationReflectionHelper"

    @native(
        "findField", "(Ljava/lang/Class;Ljava/lang/String;)Ljava/lang/reflect/Field;"
    )
    def findField(self, cls, name):
        return cls.fields[name] if hasattr(cls, name) else None

    @native("remapName", "(Lcpw/mods/modlauncher/api/INameMappingService$Domain;Ljava/lang/String;)Ljava/lang/String;")
    def remapName(self, *_):
        pass


class DeferredWorkQueue(NativeClass):
    NAME = "net/minecraftforge/fml/DeferredWorkQueue"

    @native(
        "runLater", "(Ljava/lang/Runnable;)Ljava/util/concurrent/CompletableFuture;"
    )
    def runLater(self, runnable):
        return lambda: runnable()  # todo: schedule somewhere


class ExtensionPoint(NativeClass):
    NAME = "net/minecraftforge/fml/ExtensionPoint"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "DISPLAYTEST": 0,
                "CONFIGGUIFACTORY": 1,
            }
        )


class EventNetworkChannel(NativeClass):
    NAME = "net/minecraftforge/fml/event/EventNetworkChannel"


class SidedThreadGroups(NativeClass):
    NAME = "net/minecraftforge/fml/common/thread/SidedThreadGroups"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "SERVER": 0,
                "CLIENT": 1,
            }
        )


class ModFileScanData__AnnotationData(NativeClass):
    NAME = "net/minecraftforge/forgespi/language/ModFileScanData$AnnotationData"

    @native("getMemberName", "()Ljava/lang/String;")
    def getMemberName(self, instance):
        return "unimplemented"


class SubscribeEvent(NativeClass):
    NAME = "net/minecraftforge/eventbus/api/SubscribeEvent"

    def on_annotate(self, cls, args):
        pass  # todo: implement


class BrandingControl(NativeClass):
    NAME = "net/minecraftforge/fml/BrandingControl"


class WorldEvent(NativeClass):
    NAME = "net/minecraftforge/event/world/WorldEvent"


class DatagenModLoader(NativeClass):
    NAME = "net/minecraftforge/fml/DatagenModLoader"

    @native("isRunningDataGen", "()Z", static=True)
    def isRunningDataGen(self, *_):
        return shared.data_gen


class ForgeMod(NativeClass):
    NAME = "net/minecraftforge/common/ForgeMod"

    @native("enableMilkFluid", "()V")
    def enableMilkFluid(self, *_):
        pass


class INameMappingService__Domain(NativeClass):
    NAME = "cpw/mods/modlauncher/api/INameMappingService$Domain"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "FIELD": 0,
            }
        )


class FMLLoadCompleteEvent(NativeClass):
    NAME = "net/minecraftforge/fml/event/lifecycle/FMLLoadCompleteEvent"


class TickEvent__Type(NativeClass):
    NAME = "net/minecraftforge/event/TickEvent$Type"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "WORLD": 0,
        })

    @native("values", "()[Lnet/minecraftforge/event/TickEvent$Type;")
    def values(self):
        return list(self.exposed_attributes.values())


class InterModComms(NativeClass):
    NAME = "net/minecraftforge/fml/InterModComms"

    @native("sendTo", "(Ljava/lang/String;Ljava/lang/String;Ljava/util/function/Supplier;)Z", static=True)
    def sendTo(self, a, b, supplier):
        pass
