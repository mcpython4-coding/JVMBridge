import os.path
import traceback
import typing

import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.Instructions import LambdaInvokeDynamic
from jvm.JavaExceptionStack import StackCollectingException
from jvm.natives import bind_native, bind_annotation
from mcpython import shared
from mcpython.common import config
from mcpython.common.container.ResourceStack import ItemStack
from mcpython.common.mod.util import LoadingInterruptException
from mcpython.engine import logger
from mcpython.util.enums import EnumSide

EVENT2STAGE: typing.Dict[str, str] = {
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/item/Item;>;)V": "stage:item:factory_usage",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/item/alchemy/Potion;>;)V": "stage:item:potions",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/item/enchantment/Enchantment;>;)V": "stage:item:enchantments",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/level/block/Block;>;)V": "stage:block:factory_usage",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/level/block/entity/BlockEntityType<*>;>;)V": "stage:block:bind_special",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/block/Block;>;)V": "stage:block:factory_usage",
    "Lnet/minecraftforge/fml/common/event/FMLPreInitializationEvent;": "stage:mod:init",
    "Lnet/minecraftforge/fml/common/event/FMLInitializationEvent;": "stage:mod:init",
    "Lnet/minecraftforge/fml/common/event/FMLPostInitializationEvent;": "stage:post",
    "call_side:::(Lnet/minecraftforge/fml/event/lifecycle/FMLCommonSetupEvent;)V": "stage:mod:init",
    "Lnet/minecraftforge/fml/event/lifecycle/FMLCommonSetupEvent;": "stage:mod:init",
    "Lnet/minecraftforge/client/event/ModelBakeEvent;": "stage:model:model_bake",
    "Lnet/minecraftforge/client/event/TextureStitchEvent$Pre;": "stage:textureatlas:prepare",
    "Lnet/minecraftforge/client/event/TextureStitchEvent$Post;": "stage:textureatlas:prepare",
    "Lnet/minecraftforge/fml/event/lifecycle/FMLClientSetupEvent;": "stage:client:work",
    "Lnet/minecraftforge/fml/event/config/ModConfigEvent$Loading;": "stage:mod:config:load",
    "Lnet/minecraftforge/fml/event/config/ModConfigEvent;": "stage:mod:config:work",
    "Lnet/minecraftforge/event/RegisterCommandsEvent;": "stage:commands",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/item/crafting/RecipeSerializer<*>;>;)V": "stage:recipes:serializers",
    "Lnet/minecraftforge/event/world/BiomeLoadingEvent;": "stage:worldgen:biomes",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/level/biome/Biome;>;)V": "stage:worldgen:biomes",
    "Lnet/minecraftforge/client/event/ModelRegistryEvent;": "stage:model:model_create",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/inventory/MenuType<*>;>;)V": "stage:states",
    "(Lnet/minecraftforge/event/RegistryEvent$MissingMappings<Lnet/minecraft/world/item/Item;>;)V": "stage:item:overwrite",
    "(Lnet/minecraftforge/event/RegistryEvent$MissingMappings<Lnet/minecraft/world/level/block/Block;>;)V": "stage:block:overwrite",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/level/material/Fluid;>;)V": "stage:fluids:register",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/level/levelgen/feature/StructureFeature<*>;>;)V": "stage:worldgen:feature",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/level/levelgen/feature/Feature<*>;>;)V": "stage:worldgen:feature",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/level/levelgen/surfacebuilders/SurfaceBuilder<*>;>;)V": "stage:worldgen:layer",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraftforge/common/loot/GlobalLootModifierSerializer<*>;>;)V": "stage:loottables:modify",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraftforge/registries/DataSerializerEntry;>;)V": "stage:resources:pipe:add_mapper",
    "Lnet/minecraftforge/forge/event/lifecycle/GatherDataEvent;": "special:datagen:generate",
}

missing_event_file = os.path.dirname(os.path.dirname(__file__))+"/missing_events.txt"


class Annotations:
    @staticmethod
    @bind_annotation("net/minecraftforge/fml/relauncher/IFMLLoadingPlugin$Name")
    @bind_annotation("net/minecraftforge/fml/relauncher/IFMLLoadingPlugin$MCVersion")
    @bind_annotation("net/minecraftforge/fml/relauncher/IFMLLoadingPlugin$TransformerExclusions")
    @bind_annotation("net/minecraftforge/fml/relauncher/IFMLLoadingPlugin$SortingIndex")
    @bind_annotation("net/minecraftforge/fml/relauncher/SideOnly")
    @bind_annotation("net/minecraftforge/api/distmarker/OnlyIn")
    @bind_annotation("mcp/MethodsReturnNonnullByDefault")
    @bind_annotation("net/minecraftforge/fml/common/Optional$Method")
    @bind_annotation("net/minecraftforge/fml/common/Optional$Interface")
    @bind_annotation("net/minecraftforge/common/config/Config")
    @bind_annotation("net/minecraft/MethodsReturnNonnullByDefault")
    @bind_annotation("net/minecraftforge/eventbus/api/Cancelable")
    @bind_annotation("net/minecraftforge/eventbus/api/Event$HasResult")
    @bind_annotation("net/minecraftforge/common/capabilities/CapabilityInject")
    @bind_annotation("net/minecraftforge/registries/ObjectHolder")
    @bind_annotation("com/mojang/blaze3d/MethodsReturnNonnullByDefault")
    def noAnnotationProcessing(method, stack, target, args):
        pass


def boundMethodToStage(method: AbstractMethod, event: str, mod: str):
    @shared.mod_loader(mod, event)
    async def work():
        # print(mod, event, method)
        shared.CURRENT_EVENT_SUB = mod
        try:
            method.invoke([] if method.access & 0x0008 else [None])
        except StackCollectingException as e:
            if shared.IS_CLIENT:
                traceback.print_exc()
                print(e.format_exception())

                if e.method_call_stack:
                    e.method_call_stack[0].code_repr.print_stats()

                import mcpython.common.state.LoadingExceptionViewState
                mcpython.common.state.LoadingExceptionViewState.error_occur(e.format_exception())
                raise LoadingInterruptException from None

            else:
                traceback.print_exc()
                print(e.format_exception())
                raise LoadingInterruptException


class ModContainer:
    @staticmethod
    @bind_native("net/minecraftforge/fml/loading/FMLLoader", "isProduction()Z")
    def isProduction(method, stack):
        return not shared.dev_environment

    @staticmethod
    @bind_native("net/minecraftforge/fml/ModLoadingContext", "getActiveNamespace()Ljava/lang/String;")
    def getActiveNamespace(method, stack, this):
        return shared.CURRENT_EVENT_SUB

    @staticmethod
    @bind_native("net/minecraftforge/fml/loading/FMLPaths", "get()Ljava/nio/file/Path;")
    def get(method, stack, instance):
        return shared.local

    @staticmethod
    @bind_annotation("net/minecraftforge/fml/common/Mod")
    def processModAnnotation(method, stack, target, args):
        try:
            target.create_instance().init("()V")
        except StackCollectingException as e:
            e.add_trace(method)
            if shared.IS_CLIENT:
                traceback.print_exc()
                print(e.format_exception())

                if e.method_call_stack:
                    e.method_call_stack[0].code_repr.print_stats()

                import mcpython.common.state.LoadingExceptionViewState
                mcpython.common.state.LoadingExceptionViewState.error_occur(e.format_exception())
                raise LoadingInterruptException from None

            else:
                traceback.print_exc()
                print(e.format_exception())
                raise LoadingInterruptException

    @staticmethod
    @bind_annotation("net/minecraftforge/fml/common/Mod$EventHandler")
    @bind_annotation("net/minecraftforge/fml/common/Mod$EventBusSubscriber")
    @bind_annotation("net/minecraftforge/fml/common/eventhandler/SubscribeEvent")
    @bind_annotation("net/minecraftforge/eventbus/api/SubscribeEvent")
    def processEventAnnotation(method, stack, target, args):
        if isinstance(target, AbstractMethod):
            event_name = target.signature.split(")")[0].removeprefix("(")

            try:
                signature = target.attributes["Signature"][0].signature
            except (KeyError, AttributeError):
                signature = event_name

            if signature in EVENT2STAGE and EVENT2STAGE[signature]:
                boundMethodToStage(target, EVENT2STAGE[signature], shared.CURRENT_EVENT_SUB)
                return

            if isinstance(target, LambdaInvokeDynamic.LambdaInvokeDynamicWrapper):
                signature2 = "call_side:::"+target.method.signature
                if signature2 in EVENT2STAGE and EVENT2STAGE[signature2]:
                    boundMethodToStage(target, EVENT2STAGE[signature2], shared.CURRENT_EVENT_SUB)
                    return

                logger.println("Alternative event signature for next error:", signature2)

            logger.println(f"[FML][WARN] mod {shared.CURRENT_EVENT_SUB} subscribed to event {signature} with {target}, but stage was not found")

            if os.path.exists(missing_event_file):
                with open(missing_event_file) as f:
                    data = f.read()
            else:
                data = ""

            if signature not in data:
                with open(missing_event_file, mode="a") as f:
                    f.write(f"mod {shared.CURRENT_EVENT_SUB} event {signature} with {target}\n")

    @staticmethod
    @bind_native("net/minecraftforge/eventbus/api/IEventBus", "addListener(Ljava/util/function/Consumer;)V")
    def addListener(method, stack, bus, listener):
        ModContainer.processEventAnnotation(method, stack, listener, [])

    @staticmethod
    @bind_native("net/minecraftforge/eventbus/api/IEventBus", "addGenericListener(Ljava/lang/Class;Ljava/util/function/Consumer;)V")
    def addGenericListener(method, stack, this, cls, consumer):
        print("generic listener", this, cls, consumer)

    @staticmethod
    @bind_native("net/minecraftforge/eventbus/api/IEventBus", "addGenericListener(Ljava/lang/Class;Lnet/minecraftforge/eventbus/api/EventPriority;Ljava/util/function/Consumer;)V")
    def addGenericListener(method, stack, this, cls, priority, consumer):
        ModContainer.addGenericListener(method, stack, this, cls, consumer)

    @staticmethod
    @bind_native("net/minecraftforge/eventbus/api/IEventBus", "addListener(Lnet/minecraftforge/eventbus/api/EventPriority;Ljava/util/function/Consumer;)V")
    def addListener(method, stack, bus, priority, listener):
        ModContainer.processEventAnnotation(method, stack, listener, [])

    @staticmethod
    @bind_native("net/minecraftforge/eventbus/api/IEventBus", "addListener(Lnet/minecraftforge/eventbus/api/EventPriority;ZLjava/lang/Class;Ljava/util/function/Consumer;)V")
    def addListener(method, stack, this, priority, some_flag, cls, consumer):
        ModContainer.addGenericListener(method, stack, this, cls, consumer)

    @staticmethod
    @bind_native("net/minecraftforge/fml/event/lifecycle/FMLCommonSetupEvent", "enqueueWork(Ljava/lang/Runnable;)Ljava/util/concurrent/CompletableFuture;")
    def enqueueWork(method, stack, this, target):
        boundMethodToStage(target, EVENT2STAGE["Lnet/minecraftforge/fml/event/lifecycle/FMLCommonSetupEvent;"], shared.CURRENT_EVENT_SUB)

    @staticmethod
    @bind_native("net/minecraftforge/api/distmarker/Dist", "values()[Lnet/minecraftforge/api/distmarker/Dist;")
    def distValues(method, stack):
        return method.get_class().get_enum_values()

    @staticmethod
    @bind_native("net/minecraftforge/api/distmarker/Dist", "ordinal()I")
    def ordinal(method, stack, this):
        return 0 if "client" in this else 1

    @staticmethod
    @bind_native("net/minecraftforge/fml/loading/FMLLoader", "getDist()Lnet/minecraftforge/api/distmarker/Dist;")
    def getDist(method, stack):
        cls = stack.vm.get_class("net/minecraftforge/api/distmarker/Dist")
        if shared.IS_CLIENT:
            return cls.get_static_attribute("CLIENT")

        return cls.get_static_attribute("SERVER")

    @staticmethod
    @bind_native("net/minecraftforge/fml/DistExecutor", "runForDist(Ljava/util/function/Supplier;Ljava/util/function/Supplier;)Ljava/lang/Object;")
    @bind_native("net/minecraftforge/fml/DistExecutor", "safeRunForDist(Ljava/util/function/Supplier;Ljava/util/function/Supplier;)Ljava/lang/Object;")
    @bind_native("net/minecraftforge/fml/DistExecutor", "unsafeRunForDist(Ljava/util/function/Supplier;Ljava/util/function/Supplier;)Ljava/lang/Object;")
    def runForDist(method, stack, client, server):
        if shared.IS_CLIENT:
            client.invoke([])
        server.invoke([])

    @staticmethod
    @bind_native("net/minecraftforge/fml/DistExecutor", "unsafeRunWhenOn(Lnet/minecraftforge/api/distmarker/Dist;Ljava/util/function/Supplier;)V")
    @bind_native("net/minecraftforge/fml/DistExecutor", "runWhenOn(Lnet/minecraftforge/api/distmarker/Dist;Ljava/util/function/Supplier;)V")
    @bind_native("net/minecraftforge/fml/DistExecutor", "safeRunWhenOn(Lnet/minecraftforge/api/distmarker/Dist;Ljava/util/function/Supplier;)V")
    def runWhenOn(method, stack, destination, supplier):
        if destination == "net/minecraftforge/api/distmarker/Dist::CLIENT" and not shared.IS_CLIENT: return
        supplier()

    @staticmethod
    @bind_native("net/minecraftforge/fml/javafmlmod/FMLJavaModLoadingContext", "get()Lnet/minecraftforge/fml/javafmlmod/FMLJavaModLoadingContext;")
    def getLoadingContext(method, stack):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/fml/ModLoadingContext", "registerExtensionPoint(Ljava/lang/Class;Ljava/util/function/Supplier;)V")
    def registerExtensionPoint(method, stack, this, cls, supplier):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/fml/javafmlmod/FMLJavaModLoadingContext", "getModEventBus()Lnet/minecraftforge/eventbus/api/IEventBus;")
    def getModEventBus(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/eventbus/api/IEventBus", "register(Ljava/lang/Object;)V")
    def registerArbitraryObject(method, stack, this, obj):
        obj.get_method("register", "()V").invoke([obj])

    @staticmethod
    @bind_native("net/minecraft/core/Registry", "m_122961_(Lnet/minecraft/core/Registry;Ljava/lang/String;Ljava/lang/Object;)Ljava/lang/Object;")
    @bind_native("net/minecraft/core/Registry", "m_122965_(Lnet/minecraft/core/Registry;Lnet/minecraft/resources/ResourceLocation;Ljava/lang/Object;)Ljava/lang/Object;")
    def register(method, stack, registry, name, obj):
        if isinstance(name, str):
            obj.get_method("setRegistryName", "(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;").invoke([obj, name])
        elif hasattr(name, "name"):
            obj.get_method("setRegistryName", "(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;").invoke([obj, name.name])

        obj.get_method("register", "()V").invoke([obj])

    @staticmethod
    @bind_native("net/minecraftforge/fml/ModLoadingContext", "get()Lnet/minecraftforge/fml/ModLoadingContext;")
    def getContext(method, stack):
        return method.cls.create_instance()

    @staticmethod
    @bind_native("net/minecraftforge/fml/ModLoadingContext", "registerConfig(Lnet/minecraftforge/fml/config/ModConfig$Type;Lnet/minecraftforge/fml/config/IConfigSpec;Ljava/lang/String;)V")
    @bind_native("net/minecraftforge/fml/ModLoadingContext", "registerConfig(Lnet/minecraftforge/fml/config/ModConfig$Type;Lnet/minecraftforge/fml/config/IConfigSpec;)V")
    def registerConfig(method, stack, this, mod_config_type, config_spec, some_string: str = None):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/fml/common/event/FMLPreInitializationEvent", "getModLog()Lorg/apache/logging/log4j/Logger;")
    def getModLogger(method, stack, this):
        # return stack.vm.get_class("org/apache/logging/log4j/Logger").create_instance()
        pass

    @staticmethod
    @bind_native("net/minecraftforge/registries/GameData", "register_impl(Lnet/minecraftforge/registries/IForgeRegistryEntry;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def register_impl(method, stack, obj):
        return obj

    @staticmethod
    @bind_native("net/minecraftforge/eventbus/api/EventListenerHelper", "getListenerList(Ljava/lang/Class;)Lnet/minecraftforge/eventbus/ListenerList;")
    def getListenerList(method, stack, this):
        return []

    @staticmethod
    @bind_native("net/minecraftforge/fml/common/Mod$EventBusSubscriber$Bus", "bus()Ljava/util/function/Supplier;")
    def getBus(method, stack, this):
        return lambda: None

    @staticmethod
    @bind_native("net/minecraftforge/fml/loading/FMLConfig", "defaultConfigPath()Ljava/lang/String;")
    def defaultConfigPath(method, stack, this=None):
        return shared.local+"/jvm_config"

    @staticmethod
    @bind_native("net/minecraftforge/fml/ModList", "get()Lnet/minecraftforge/fml/ModList;")
    def getModList(method, stack):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/fml/ModList", "isLoaded(Ljava/lang/String;)Z")
    def isModLoaded(method, stack, this, name):
        return name in shared.mod_loader.mods

    @staticmethod
    @bind_native("net/minecraftforge/registries/IForgeRegistry", "getValues()Ljava/util/Collection;")
    def getValues(method, stack, this):
        obj = stack.vm.get_class("java/util/List").create_instance().init("()V")
        obj.underlying = []  # todo: fetch stuff here
        return obj

    @staticmethod
    @bind_native("net/minecraftforge/event/RegistryEvent$Register", "getRegistry()Lnet/minecraftforge/registries/IForgeRegistry;")
    def getRegistry(method, stack, this):
        return "dummy:registry"

    @staticmethod
    @bind_native("net/minecraftforge/registries/ForgeRegistryEntry", "setRegistryName(Lnet/minecraft/resources/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name):
        this.registry_name = name.name
        return this

    @staticmethod
    @bind_native("net/minecraft/core/Registry", "m_6579_()Ljava/util/Set;")
    def m_6579_(method, stack, this):
        return stack.vm.get_class("java/util/Set").create_instance().init("()V")


class Configs:
    @staticmethod
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "<init>()V")
    def init(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "comment(Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "comment([Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "push(Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "defineEnum(Ljava/lang/String;Ljava/lang/Enum;)Lnet/minecraftforge/common/ForgeConfigSpec$EnumValue;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "define(Ljava/lang/String;Z)Lnet/minecraftforge/common/ForgeConfigSpec$BooleanValue;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "define(Ljava/lang/String;Ljava/lang/Object;)Lnet/minecraftforge/common/ForgeConfigSpec$ConfigValue;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "pop()Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "build()Lnet/minecraftforge/common/ForgeConfigSpec;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "defineInRange(Ljava/lang/String;III)Lnet/minecraftforge/common/ForgeConfigSpec$IntValue;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "defineList(Ljava/lang/String;Ljava/util/List;Ljava/util/function/Predicate;)Lnet/minecraftforge/common/ForgeConfigSpec$ConfigValue;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "worldRestart()Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "translation(Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "defineInRange(Ljava/lang/String;DDD)Lnet/minecraftforge/common/ForgeConfigSpec$DoubleValue;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "defineListAllowEmpty(Ljava/util/List;Ljava/util/function/Supplier;Ljava/util/function/Predicate;)Lnet/minecraftforge/common/ForgeConfigSpec$ConfigValue;")
    def anyUnused(method, stack, this, *_):
        return this

    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "configure(Ljava/util/function/Function;)Lorg/apache/commons/lang3/tuple/Pair;")
    def configure(self, method, stack, this):
        return None, None


class Capabilities:
    @staticmethod
    @bind_native("net/minecraftforge/common/capabilities/CapabilityToken", "<init>()V")
    def init(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/common/capabilities/CapabilityManager", "get(Lnet/minecraftforge/common/capabilities/CapabilityToken;)Lnet/minecraftforge/common/capabilities/Capability;")
    def getCapabilities(method, stack, token):
        return stack.vm.get_class("net/minecraftforge/common/capabilities/Capability").create_instance()


class ItemCreation:
    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "<init>()V")
    @bind_native("net/minecraft/item/Item$Properties", "<init>()V")
    @bind_native("net/minecraft/world/food/FoodProperties$Builder", "<init>()V")
    def initProperties(method, stack, this):
        this.bound_tab = None
        this.rarity = -1

    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "m_41489_(Lnet/minecraft/world/food/FoodProperties;)Lnet/minecraft/world/item/Item$Properties;")
    def createFrom(method, stack, this, other):
        this.bound_tab = other.bound_tab
        this.rarity = other.rarity
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "m_41491_(Lnet/minecraft/world/item/CreativeModeTab;)Lnet/minecraft/world/item/Item$Properties;")
    @bind_native("net/minecraft/item/Item$Properties", "func_200916_a(Lnet/minecraft/item/ItemGroup;)Lnet/minecraft/item/Item$Properties;")
    def setItemTab(method, stack, this, tab):
        if this is not None:
            this.bound_tab = tab

        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "m_41497_(Lnet/minecraft/world/item/Rarity;)Lnet/minecraft/world/item/Item$Properties;")
    def setRarity(method, stack, this, rarity):
        this.rarity = rarity  # todo: parse rarity for item
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "setNoRepair()Lnet/minecraft/world/item/Item$Properties;")
    def setNoRepair(method, stack, this):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "m_41486_()Lnet/minecraft/world/item/Item$Properties;")
    def m_41486_(method, stack, this):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "m_41499_(I)Lnet/minecraft/world/item/Item$Properties;")
    def m_41499_(method, stack, this, v: int):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "m_41487_(I)Lnet/minecraft/world/item/Item$Properties;")
    def setSomeInt(method, stack, this, value: int):
        return this  # todo: do something with value

    @staticmethod
    @bind_native("net/minecraft/world/food/FoodProperties$Builder", "m_38758_(F)Lnet/minecraft/world/food/FoodProperties$Builder;")
    @bind_native("net/minecraft/world/food/FoodProperties$Builder", "m_38765_()Lnet/minecraft/world/food/FoodProperties$Builder;")
    @bind_native("net/minecraft/world/food/FoodProperties$Builder", "m_38760_(I)Lnet/minecraft/world/food/FoodProperties$Builder;")
    @bind_native("net/minecraft/world/food/FoodProperties$Builder", "m_38767_()Lnet/minecraft/world/food/FoodProperties;")
    def setSomeProperty(method, stack, this, *args):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "m_41495_(Lnet/minecraft/world/item/Item;)Lnet/minecraft/world/item/Item$Properties;")
    def bindSomeItem(method, stack, this, item):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item", "<init>(Lnet/minecraft/world/item/Item$Properties;)V")
    def initItem(method, stack, this, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/RecordItem", "<init>(ILjava/util/function/Supplier;Lnet/minecraft/world/item/Item$Properties;)V")
    def initRecordItem(method, stack, this, some_int, supplier, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/BoatItem", "<init>(Ljava/util/function/Supplier;Lnet/minecraft/world/item/Item$Properties;)V")
    @bind_native("net/minecraft/world/item/BoatItem", "<init>(Lnet/minecraft/world/entity/vehicle/Boat$Type;Lnet/minecraft/world/item/Item$Properties;)V")
    def initBoatItem(method, stack, this, supplier, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/BucketItem", "<init>(Ljava/util/function/Supplier;Lnet/minecraft/world/item/Item$Properties;)V")
    def initBucketItem(method, stack, this, supplier, properties):
        this.properties = properties
        this.registry_name = None
        from mcpython.common.item.BucketItem import BucketItem
        this.base_classes = [BucketItem]

    @staticmethod
    @bind_native("net/minecraft/world/item/StandingAndWallBlockItem", "<init>(Lnet/minecraft/world/level/block/Block;Lnet/minecraft/world/level/block/Block;Lnet/minecraft/world/item/Item$Properties;)V")
    def initStandingAndWallSignBlockItem(method, stack, this, standing, wall, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/BlockItem", "<init>(Lnet/minecraft/world/level/block/Block;Lnet/minecraft/world/item/Item$Properties;)V")
    @bind_native("net/minecraft/item/BlockItem", "<init>(Lnet/minecraft/block/Block;Lnet/minecraft/item/Item$Properties;)V")
    @bind_native("net/minecraft/item/ItemBlock", "<init>(Lnet/minecraft/block/Block;)V")
    def initBlockItem(method, stack, this, block, properties=None):
        this.properties = properties
        try:
            this.registry_name = None if block is None else block.registry_name
        except AttributeError:
            print("error during constructing block-item", block)
            this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/SpawnEggItem", "<init>(Lnet/minecraft/world/entity/EntityType;IILnet/minecraft/world/item/Item$Properties;)V")
    def initSpawnEggItem(method, stack, this, entity_type, int_a, int_b, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/SwordItem", "<init>(Lnet/minecraft/world/item/Tier;IFLnet/minecraft/world/item/Item$Properties;)V")
    def initSwordItem(method, stack, this, item_tier, durability, damage, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/PickaxeItem", "<init>(Lnet/minecraft/world/item/Tier;IFLnet/minecraft/world/item/Item$Properties;)V")
    def initPickaxeItem(method, stack, this, item_tier, durability, damage, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/AxeItem", "<init>(Lnet/minecraft/world/item/Tier;FFLnet/minecraft/world/item/Item$Properties;)V")
    def initAxeItem(method, stack, this, item_tier, durability, damage, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/ShovelItem", "<init>(Lnet/minecraft/world/item/Tier;FFLnet/minecraft/world/item/Item$Properties;)V")
    def initShovelItem(method, stack, this, item_tier, durability, damage, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/HoeItem", "<init>(Lnet/minecraft/world/item/Tier;IFLnet/minecraft/world/item/Item$Properties;)V")
    def initHoeItem(method, stack, this, item_tier, durability, damage, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/ArmorItem", "<init>(Lnet/minecraft/world/item/ArmorMaterial;Lnet/minecraft/world/entity/EquipmentSlot;Lnet/minecraft/world/item/Item$Properties;)V")
    def initArmorItem(method, stack, this, material, slot, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/Item", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/RecordItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/BoatItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/BucketItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/BlockItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/item/BlockItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/StandingAndWallBlockItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/SpawnEggItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/SwordItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/PickaxeItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/AxeItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/ShovelItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/HoeItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/ArmorItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name: str):
        this.registry_name = name if ":" in name else (shared.CURRENT_EVENT_SUB + ":" + name)
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item", "setRegistryName(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/BlockItem", "setRegistryName(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName2(method, stack, this, namespace, name):
        this.registry_name = namespace + ":" + name
        return this

    @staticmethod
    @bind_native("net/minecraft/item/ItemBlock", "setRegistryName(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/item/Item", "setRegistryName(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/BlockItem", "setRegistryName(Lnet/minecraft/resources/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/SpawnEggItem", "setRegistryName(Lnet/minecraft/resources/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryNameFromResourceLocation(method, stack, this, resource_location):
        this.registry_name = resource_location.name if resource_location is not None else None
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item", "getRegistryName()Lnet/minecraft/resources/ResourceLocation;")
    @bind_native("net/minecraft/world/item/BlockItem", "getRegistryName()Lnet/minecraft/resources/ResourceLocation;")
    def getRegistryName(method, stack, obj):
        return stack.vm.get_class("net/minecraft/resources/ResourceLocation").create_instance().init("(Ljava/lang/String;)V", obj.registry_name)

    @staticmethod
    @bind_native("net/minecraft/world/item/Item", "register()V")
    @bind_native("net/minecraft/world/item/RecordItem", "register()V")
    @bind_native("net/minecraft/world/item/BoatItem", "register()V")
    @bind_native("net/minecraft/world/item/BucketItem", "register()V")
    @bind_native("net/minecraft/world/item/BlockItem", "register()V")
    @bind_native("net/minecraft/item/BlockItem", "register()V")
    @bind_native("net/minecraft/world/item/StandingAndWallBlockItem", "register()V")
    @bind_native("net/minecraft/world/item/SpawnEggItem", "register()V")
    @bind_native("net/minecraft/world/item/SwordItem", "register()V")
    @bind_native("net/minecraft/world/item/PickaxeItem", "register()V")
    @bind_native("net/minecraft/world/item/AxeItem", "register()V")
    @bind_native("net/minecraft/world/item/ShovelItem", "register()V")
    @bind_native("net/minecraft/world/item/HoeItem", "register()V")
    @bind_native("net/minecraft/world/item/ArmorItem", "register()V")
    def register(method, stack, this):
        if this.get_class().name != "net/minecraft/world/item/BlockItem":
            from mcpython.common.factory.ItemFactory import ItemFactory

            instance = ItemFactory().set_name(this.registry_name)

            if hasattr(this, "base_classes"):
                for cls in this.base_classes:
                    instance.add_base_class(cls)

            instance.finish()

        try:
            if this.properties.bound_tab is not None:
                @shared.mod_loader(shared.CURRENT_EVENT_SUB, "stage:item_groups:load")
                def bind_to_tab():
                    try:
                        this.properties.bound_tab.instance.group.add(this.registry_name)
                    except ValueError:
                        pass
        except AttributeError:
            pass

    @staticmethod
    @bind_native("net/minecraft/item/ItemGroup", "<init>(Ljava/lang/String;)V")
    def init(method, stack, this, name):
        from mcpython.common.container.ItemGroup import ItemGroup
        this.underlying = ItemGroup()

    @staticmethod
    @bind_native("net/minecraft/world/item/CreativeModeTab", "<init>(ILjava/lang/String;)V")
    def initCreativeTab(method, stack, this, some_id, name: str):
        ItemCreation.initCreativeTabWithName(method, stack, this, name)

    @staticmethod
    @bind_native("net/minecraft/world/item/CreativeModeTab", "<init>(Ljava/lang/String;)V")
    def initCreativeTabWithName(method, stack, this, name: str):
        if shared.IS_CLIENT:
            import mcpython.client.gui.InventoryCreativeTab
            tab = mcpython.client.gui.InventoryCreativeTab.CreativeItemTab(name, ItemStack("minecraft:barrier"))
            this.instance = tab

            mcpython.client.gui.InventoryCreativeTab.CT_MANAGER.add_tab(tab)

    @staticmethod
    @bind_native("net/minecraft/creativetab/CreativeTabs", "<init>(Ljava/lang/String;)V")
    def initCreativeTabOld(method, stack, this, name: str):
        import mcpython.client.gui.InventoryCreativeTab

        tab = mcpython.client.gui.InventoryCreativeTab.CreativeItemTab(name, ItemStack("minecraft:barrier"))
        this.instance = tab

        mcpython.client.gui.InventoryCreativeTab.CT_MANAGER.add_tab(tab)

    @staticmethod
    @bind_native("net/minecraft/world/item/Item", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/BlockItem", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def getInstance(method, stack, this):
        return this


class ItemStackImpl:
    @staticmethod
    @bind_native("net/minecraft/world/item/ItemStack", "<init>(Lnet/minecraft/world/level/ItemLike;)V")
    def initItemStack(method, stack, this, item_like):
        this.underlying = ItemStack()


class ItemTier:
    @staticmethod
    @bind_native("net/minecraftforge/common/ForgeTier", "<init>(IIFFILnet/minecraft/tags/Tag;Ljava/util/function/Supplier;)V")
    def init(method, stack, this, int_a, int_b, float_a, float_b, int_c, tag, supplier):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/common/TierSortingRegistry", "registerTier(Lnet/minecraft/world/item/Tier;Lnet/minecraft/resources/ResourceLocation;Ljava/util/List;Ljava/util/List;)Lnet/minecraft/world/item/Tier;")
    def registerTier(method, stack, tier, name, list_a, list_b):
        return tier


class BlockCreation:
    @staticmethod
    @bind_native("net/minecraft/world/level/block/Block", "m_49796_(DDDDDD)Lnet/minecraft/world/phys/shapes/VoxelShape;")
    @bind_native("net/minecraft/world/phys/shapes/Shapes", "m_83048_(DDDDDD)Lnet/minecraft/world/phys/shapes/VoxelShape;")
    def createVoxelShape(method, stack, *some_values):
        pass

    @staticmethod
    @bind_native("net/minecraft/util/math/AxisAlignedBB", "<init>(DDDDDD)V")
    def initVoxelShape(method, stack, this, *values):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/phys/shapes/Shapes", "m_83110_(Lnet/minecraft/world/phys/shapes/VoxelShape;Lnet/minecraft/world/phys/shapes/VoxelShape;)Lnet/minecraft/world/phys/shapes/VoxelShape;")
    def combine(method, stack, a, b):
        return a

    @staticmethod
    @bind_native("net/minecraft/world/phys/shapes/Shapes", "m_83144_()Lnet/minecraft/world/phys/shapes/VoxelShape;")
    def m_83144_(method, stack):
        return stack.vm.get_class("net/minecraft/world/phys/shapes/VoxelShape").create_instance()

    @staticmethod
    @bind_native("net/minecraft/world/level/material/Material$Builder", "<init>(Lnet/minecraft/world/level/material/MaterialColor;)V")
    def init(method, stack, this, color):
        this.material_color = color

    @staticmethod
    @bind_native("net/minecraft/world/level/material/Material$Builder", "m_76354_()Lnet/minecraft/world/level/material/Material$Builder;")
    @bind_native("net/minecraft/world/level/material/Material$Builder", "m_76360_()Lnet/minecraft/world/level/material/Material$Builder;")
    @bind_native("net/minecraft/world/level/material/Material$Builder", "m_76353_()Lnet/minecraft/world/level/material/Material$Builder;")
    @bind_native("net/minecraft/world/level/material/Material$Builder", "m_76357_()Lnet/minecraft/world/level/material/Material$Builder;")
    @bind_native("net/minecraft/world/level/material/Material$Builder", "m_76356_()Lnet/minecraft/world/level/material/Material$Builder;")
    @bind_native("net/minecraft/world/level/material/Material$Builder", "m_76350_()Lnet/minecraft/world/level/material/Material$Builder;")
    def setSomeFlag(method, stack, this):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/material/Material$Builder", "m_76359_()Lnet/minecraft/world/level/material/Material;")
    def build(method, stack, this):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60926_(Lnet/minecraft/world/level/block/state/BlockBehaviour;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    def copyFrom(method, stack, behaviour):
        if behaviour is not None:
            behaviour.hardness = 1, 1
        return behaviour

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60939_(Lnet/minecraft/world/level/material/Material;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60944_(Lnet/minecraft/world/level/material/Material;Lnet/minecraft/world/level/material/MaterialColor;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    def createForMaterial(method, stack, material, color=None):
        instance = method.get_class().create_instance().init("(Lnet/minecraft/world/level/material/Material;)V", material)
        instance.material_color = color
        return instance

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60947_(Lnet/minecraft/world/level/material/Material;Ljava/util/function/Function;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    def createForMaterial(method, stack, material, function):
        instance = method.get_class().create_instance().init("(Lnet/minecraft/world/level/material/Material;)V", material)
        return instance

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "<init>(Lnet/minecraft/world/level/material/Material;)V")
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "<init>()V")
    def createForMaterial(method, stack, this, material=None):
        this.material = material
        this.material_color = None
        this.sound = None
        this.hardness = 1, 1

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60918_(Lnet/minecraft/world/level/block/SoundType;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    @bind_native("net/minecraft/world/level/block/AmethystClusterBlock", "m_60918_(Lnet/minecraft/world/level/block/SoundType;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    def setSound(method, stack, this, sound):
        this.sound = sound
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60913_(FF)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    def setHardness(method, stack, this, hardness, blast_resistance):
        this.hardness = hardness, blast_resistance
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60953_(Ljava/util/function/ToIntFunction;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60999_()Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    def onlyDropsWithCorrectTool(method, stack, this, some_function=None):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60991_(Lnet/minecraft/world/level/block/state/BlockBehaviour$StatePredicate;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    def setEmissiveRendering(method, stack, this, state_predicate):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60966_()Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    def enableInstaBreak(method, stack, this):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60955_()Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    def setNoOcclusion(method, stack, this):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60910_()Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60977_()Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60993_()Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60978_(F)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60922_(Lnet/minecraft/world/level/block/state/BlockBehaviour$StateArgumentPredicate;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60971_(Lnet/minecraft/world/level/block/state/BlockBehaviour$StatePredicate;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60960_(Lnet/minecraft/world/level/block/state/BlockBehaviour$StatePredicate;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    @bind_native("net/minecraft/world/level/block/state/BlockBehaviour$Properties", "m_60924_(Lnet/minecraft/world/level/block/state/BlockBehaviour$StatePredicate;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    def setSomeFlag(method, stack, this, *value):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/material/Material", "<init>(Lnet/minecraft/world/level/material/MaterialColor;ZZZZZZLnet/minecraft/world/level/material/PushReaction;)V")
    def initMaterial(method, stack, this, color, *values):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/level/block/Block", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/WallBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/GrassBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/AmethystBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/HugeMushroomBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/CarpetBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/MossBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/LeavesBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/RotatedPillarBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/FenceBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/FenceGateBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/DoorBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/TrapDoorBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/WoodButtonBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/TallFlowerBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/VineBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/MultifaceBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/BushBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/HorizontalDirectionalBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/DoublePlantBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/PipeBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/OreBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/BaseEntityBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/world/level/block/IronBarsBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    @bind_native("net/minecraft/block/Block", "<init>(Lnet/minecraft/block/material/Material;)V")
    @bind_native("net/minecraft/block/BlockContainer", "<init>(Lnet/minecraft/block/material/Material;)V")
    def initBlock(method, stack, this, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/PressurePlateBlock", "<init>(Lnet/minecraft/world/level/block/PressurePlateBlock$Sensitivity;Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initPressurePlate(method, stack, this, sensitivity, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/LiquidBlock", "<init>(Ljava/util/function/Supplier;Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initLiquidBlock(method, stack, this, liquid_supplier, properties):
        this.liquid_supplier = liquid_supplier
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.is_fluid = True
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/SandBlock", "<init>(ILnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initSandBlock(method, stack, this, some_int, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = True
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/StairBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initStairBlock(method, stack, this, state, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/StandingSignBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;Lnet/minecraft/world/level/block/state/properties/WoodType;)V")
    def initStandingSignBlock(method, stack, this, properties, wood_type):
        this.properties = properties
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/WallSignBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;Lnet/minecraft/world/level/block/state/properties/WoodType;)V")
    def initStandingSignBlock(method, stack, this, properties, wood_type):
        this.properties = properties
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/SlabBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initSlabBlock(method, stack, this, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = True
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/Blocks", "m_50788_(Lnet/minecraft/world/level/material/MaterialColor;Lnet/minecraft/world/level/material/MaterialColor;)Lnet/minecraft/world/level/block/RotatedPillarBlock;")
    def createLog(method, stack, material_color_1, material_color_2):
        properties = stack.vm.get_class("net/minecraft/world/level/block/state/BlockBehaviour$Properties").create_instance().init("()V")
        instance = stack.vm.get_class("net/minecraft/world/level/block/RotatedPillarBlock").create_instance().init("(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V", properties)
        properties.is_log = True
        instance.model_state = None
        return instance

    @staticmethod
    @bind_native("net/minecraft/world/level/block/SaplingBlock", "<init>(Lnet/minecraft/world/level/block/grower/AbstractTreeGrower;Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initSaplingBlock(method, stack, this, tree_grower, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/FlowerBlock", "<init>(Lnet/minecraft/world/effect/MobEffect;ILnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initFlowerBlock(method, stack, this, effect, some_int, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/GrowingPlantHeadBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;Lnet/minecraft/core/Direction;Lnet/minecraft/world/phys/shapes/VoxelShape;ZD)V")
    @bind_native("net/minecraft/world/level/block/GrowingPlantBodyBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;Lnet/minecraft/core/Direction;Lnet/minecraft/world/phys/shapes/VoxelShape;ZD)V")
    @bind_native("net/minecraft/world/level/block/GrowingPlantBodyBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;Lnet/minecraft/core/Direction;Lnet/minecraft/world/phys/shapes/VoxelShape;Z)V")
    def initGrowingPlantHeadBlock(method, stack, this, properties, direction, shape, b, v=None):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/PipeBlock", "<init>(FLnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initGrowingPlantHeadBlock(method, stack, this, some_float, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/MushroomBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;Ljava/util/function/Supplier;)V")
    def initMushroomBlock(method, stack, this, properties, supplier):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/AmethystClusterBlock", "<init>(IILnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initAmethystClusterBlock(method, stack, this, a, b, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/AmethystClusterBlock", "m_60953_(Ljava/util/function/ToIntFunction;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;")
    def someWeirdFunction(method, stack, this, function):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/FlowerPotBlock", "<init>(Lnet/minecraft/world/level/block/Block;Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initFlowerPotBlock(method, stack, this, block, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/AbstractGlassBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initAbstractGlassBlock(method, stack, this, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/LanternBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initLanternBlock(method, stack, this, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False
        this.model_state = "hanging=false"

    @staticmethod
    @bind_native("net/minecraft/world/level/block/ChainBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initLanternBlock(method, stack, this, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = True
        this.model_state = None

    @staticmethod
    @bind_native("net/minecraft/world/level/block/Block", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/LiquidBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/SandBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/StairBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/SlabBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/WallBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/GrassBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/AmethystBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/HugeMushroomBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/CarpetBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/MossBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/SaplingBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/LeavesBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/RotatedPillarBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/FenceBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/FenceGateBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/DoorBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/TrapDoorBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/PressurePlateBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/WoodButtonBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/FlowerBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/TallFlowerBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/VineBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/GrowingPlantHeadBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/GrowingPlantBodyBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/MultifaceBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/BushBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/HorizontalDirectionalBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/DoublePlantBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/PipeBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/MushroomBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/AmethystClusterBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/FlowerPotBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/OreBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/block/Block", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/BaseEntityBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/block/BlockContainer", "func_149663_c(Ljava/lang/String;)Lnet/minecraft/block/Block;")
    @bind_native("net/minecraft/block/BlockContainer", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/block/StandingSignBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/block/WallSignBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/block/IronBarsBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/LanternBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/ChainBlock", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name):
        this.registry_name = name if ":" in name else shared.CURRENT_EVENT_SUB + ":" + name
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/Block", "setRegistryName(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/AbstractGlassBlock", "setRegistryName(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName2(method, stack, this, namespace: str, name: str):
        this.registry_name = namespace + ":" + name
        return this

    @staticmethod
    @bind_native("net/minecraft/block/Block", "getRegistryName()Lnet/minecraft/util/ResourceLocation;")
    @bind_native("net/minecraft/world/level/block/Block", "getRegistryName()Lnet/minecraft/resources/ResourceLocation;")
    @bind_native("net/minecraft/block/BlockContainer", "getRegistryName()Lnet/minecraft/util/ResourceLocation;")
    @bind_native("net/minecraft/world/level/block/LanternBlock", "getRegistryName()Lnet/minecraft/resources/ResourceLocation;")
    @bind_native("net/minecraft/world/level/block/ChainBlock", "getRegistryName()Lnet/minecraft/resources/ResourceLocation;")
    def getRegistryName(method, stack, this):
        return stack.vm.get_class(method.signature.split(")")[-1][1:-1]).create_instance().init("(Ljava/lang/String;)V", this.registry_name)

    @staticmethod
    @bind_native("net/minecraft/block/Block", "func_149663_c(Ljava/lang/String;)Lnet/minecraft/block/Block;")
    def setTranslationComponentName(method, stack, this, name):
        return this

    @staticmethod
    @bind_native("net/minecraft/block/Block", "func_149647_a(Lnet/minecraft/creativetab/CreativeTabs;)Lnet/minecraft/block/Block;")
    @bind_native("net/minecraft/block/BlockContainer", "func_149647_a(Lnet/minecraft/creativetab/CreativeTabs;)Lnet/minecraft/block/Block;")
    def bindToCreativeTab(method, stack, this, tab):

        @shared.mod_loader(shared.CURRENT_EVENT_SUB, "stage:item_groups:load")
        def add_to_tab():
            tab.underlying.group.add(this.registry_name)

        return this

    @staticmethod
    @bind_native("net/minecraft/block/Block", "func_149711_c(F)Lnet/minecraft/block/Block;")
    @bind_native("net/minecraft/block/BlockContainer", "func_149711_c(F)Lnet/minecraft/block/Block;")
    @bind_native("net/minecraft/block/Block", "func_149752_b(F)Lnet/minecraft/block/Block;")
    @bind_native("net/minecraft/block/BlockContainer", "func_149752_b(F)Lnet/minecraft/block/Block;")
    @bind_native("net/minecraft/block/Block", "func_149672_a(Lnet/minecraft/block/SoundType;)Lnet/minecraft/block/Block;")
    def setSomeProperty(method, stack, this, *args):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/Block", "m_49966_()Lnet/minecraft/world/level/block/state/BlockState;")
    @bind_native("net/minecraft/world/level/block/LanternBlock", "m_49966_()Lnet/minecraft/world/level/block/state/BlockState;")
    def getDefaultBlockState(method, stack, this):
        return this.model_state if hasattr(this, "model_state") else {}

    @staticmethod
    @bind_native("net/minecraft/world/level/block/LanternBlock", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    def setDefaultBlockState(method, stack, this, state):
        this.model_state = state

    @staticmethod
    @bind_native("net/minecraft/world/level/block/Block", "register()V")
    @bind_native("net/minecraft/world/level/block/LiquidBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/SandBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/StairBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/SlabBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/WallBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/GrassBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/AmethystBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/HugeMushroomBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/CarpetBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/MossBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/SaplingBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/LeavesBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/RotatedPillarBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/FenceBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/FenceGateBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/DoorBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/TrapDoorBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/PressurePlateBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/WoodButtonBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/FlowerBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/TallFlowerBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/VineBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/GrowingPlantHeadBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/GrowingPlantBodyBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/MultifaceBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/BushBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/HorizontalDirectionalBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/DoublePlantBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/PipeBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/MushroomBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/AmethystClusterBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/FlowerPotBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/OreBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/BaseEntityBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/StandingSignBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/WallSignBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/IronBarsBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/AbstractGlassBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/LanternBlock", "register()V")
    @bind_native("net/minecraft/world/level/block/ChainBlock", "register()V")
    def register(method, stack, this):
        from mcpython.common.factory.BlockFactory import BlockFactory
        factory = BlockFactory().set_name(this.registry_name)

        try:
            if this.is_falling:
                factory.set_fall_able()
        except AttributeError:
            pass

        try:
            if this.is_slab:
                factory.set_slab()
        except AttributeError:
            pass

        try:
            if this.is_log:
                factory.set_log()
        except AttributeError:
            pass

        try:
            if this.is_fluid:
                factory.set_fluid_block()
        except AttributeError:
            pass

        if this.properties is not None:
            try:
                if this.properties.is_log:
                    factory.set_log()
            except AttributeError:
                pass

            factory.set_strength(*this.properties.hardness)

        if hasattr(this, "model_state") and this.model_state is not None:
            factory.set_default_model_state(this.model_state)

        this.internal = factory.finish()

    @staticmethod
    @bind_native("net/minecraft/world/level/block/LiquidBlock", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    @bind_native("net/minecraft/world/level/block/SaplingBlock", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    @bind_native("net/minecraft/world/level/block/HorizontalDirectionalBlock", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    @bind_native("net/minecraft/world/level/block/DoublePlantBlock", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    @bind_native("net/minecraft/world/level/block/Block", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    @bind_native("net/minecraft/world/level/block/PipeBlock", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    def registerDefaultState(method, stack, this, state):
        pass  # todo: write this into the block class itself!

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/StateDefinition", "m_61090_()Lnet/minecraft/world/level/block/state/StateHolder;")
    def getStateHolders(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/BlockState", "m_61124_(Lnet/minecraft/world/level/block/state/properties/Property;Ljava/lang/Comparable;)Ljava/lang/Object;")
    def setValue(method, stack, this, key, value):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/Block", "m_60590_()Lnet/minecraft/world/level/material/MaterialColor;")
    def defaultMaterialColor(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/level/block/Block", "m_49965_()Lnet/minecraft/world/level/block/state/StateDefinition;")
    def getStateDefinition(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/level/block/Block", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/OreBlock", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/DoorBlock", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/BaseEntityBlock", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/TrapDoorBlock", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/FenceBlock", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/FenceGateBlock", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/StandingSignBlock", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/WallSignBlock", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/IronBarsBlock", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/SlabBlock", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/level/block/GrassBlock", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def getValue(method, stack, this):
        return this


class FluidCreation:
    @staticmethod
    @bind_native("net/minecraftforge/fluids/FluidRegistry", "enableUniversalBucket()V")
    def enableUniversalBucket(method, stack, *_):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/fluids/FluidRegistry", "addBucketForFluid(Lnet/minecraftforge/fluids/Fluid;)Z")
    def addBucketForFluid(method, stack, *_):
        return True

    @staticmethod
    @bind_native("net/minecraftforge/fluids/Fluid", "<init>(Ljava/lang/String;Lnet/minecraft/util/ResourceLocation;Lnet/minecraft/util/ResourceLocation;)V")
    def init(method, stack, this, name: str, still, flowing):
        pass


class ForgeRegistries:
    @staticmethod
    @bind_native("net/minecraftforge/registries/IForgeRegistry", "register(Lnet/minecraftforge/registries/IForgeRegistryEntry;)V")
    def register(method, stack, this, obj):
        if obj is None: return
        obj.get_method("register", "()V").invoke([obj], stack=stack)

    @staticmethod
    @bind_native("net/minecraftforge/fmllegacy/RegistryObject", "of(Lnet/minecraft/resources/ResourceLocation;Lnet/minecraftforge/registries/IForgeRegistry;)Lnet/minecraftforge/fmllegacy/RegistryObject;")
    def getObjectByName(method, stack, name, registry):
        if registry is None:
            return method.cls.create_instance()

        raise RuntimeError

    @staticmethod
    @bind_native("net/minecraftforge/fml/RegistryObject", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def getObject(method, stack, this):
        return this


class ResourceLocation:
    @staticmethod
    @bind_native("net/minecraft/resources/ResourceLocation", "<init>()V")
    @bind_native("net/minecraft/util/ResourceLocation", "<init>()V")
    def init(method, stack, this):
        this.name = "minecraft:missing_name"

    @staticmethod
    @bind_native("net/minecraft/resources/ResourceLocation", "<init>(Ljava/lang/String;Ljava/lang/String;)V")
    @bind_native("net/minecraft/util/ResourceLocation", "<init>(Ljava/lang/String;Ljava/lang/String;)V")
    def init(method, stack, this, namespace, name):
        try:
            this.name = namespace + ":" + name
        except TypeError:
            raise

    @staticmethod
    @bind_native("net/minecraft/util/ResourceLocation", "<init>(Ljava/lang/String;)V")
    @bind_native("net/minecraft/resources/ResourceLocation", "<init>(Ljava/lang/String;)V")
    def init(method, stack, this, name):
        this.name = name if ":" in name else shared.CURRENT_EVENT_SUB + ":" + name

    @staticmethod
    @bind_native("net/minecraft/resources/ResourceLocation", "toString()Ljava/lang/String;")
    def toString(method, stack, this):
        return this.name

    @staticmethod
    @bind_native("net/minecraft/resources/ResourceLocation", "m_135827_()Ljava/lang/String;")
    def getNamespace(method, stack, this):
        return this.name.split(":")[0]

    @staticmethod
    @bind_native("net/minecraft/resources/ResourceLocation", "m_135815_()Ljava/lang/String;")
    @bind_native("net/minecraft/util/ResourceLocation", "m_135815_()Ljava/lang/String;")
    def getUnlocalizedName(method, stack, this):
        return this.name.split(":")[1]

    @staticmethod
    @bind_native("net/minecraft/resources/ResourceKey", "m_135785_(Lnet/minecraft/resources/ResourceKey;Lnet/minecraft/resources/ResourceLocation;)Lnet/minecraft/resources/ResourceKey;")
    def createFromKeyLocationPair(method, stack, key, location):
        return method.get_class().create_instance()

    @staticmethod
    @bind_native("net/minecraft/resources/ResourceLocation", "equals(Ljava/lang/Object;)Z")
    def equals(method, stack, this, other):
        if this is None or other is None: return False
        return this.name == other.name


class SoundType:
    @staticmethod
    @bind_native("net/minecraft/world/level/block/SoundType", "<init>(FFLnet/minecraft/sounds/SoundEvent;Lnet/minecraft/sounds/SoundEvent;Lnet/minecraft/sounds/SoundEvent;Lnet/minecraft/sounds/SoundEvent;Lnet/minecraft/sounds/SoundEvent;)V")
    def init(method, stack, this, *config):
        pass


class WorldGen:
    @staticmethod
    @bind_native("net/minecraft/world/level/block/grower/AbstractTreeGrower", "<init>()V")
    @bind_native("net/minecraft/world/level/block/grower/AbstractMegaTreeGrower", "<init>()V")
    def init(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/common/world/ForgeWorldType", "<init>(Lnet/minecraftforge/common/world/ForgeWorldType$IBasicChunkGeneratorFactory;)V")
    def init(method, stack, this, chunk_generator):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/common/world/ForgeWorldType", "setRegistryName(Lnet/minecraft/resources/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegime(method, stack, this, name):
        this.registry_name = name
        return this

    @staticmethod
    @bind_native("net/minecraftforge/common/world/ForgeWorldType", "register()V")
    def register(method, stack, this):
        pass


class Effect:
    @staticmethod
    @bind_native("net/minecraft/world/effect/MobEffect", "<init>(Lnet/minecraft/world/effect/MobEffectCategory;I)V")
    def initMobEffect(method, stack, this, cat):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/effect/MobEffect", "m_8093_()Z")
    def isInstantenous(method, stack, this):
        return True

    @staticmethod
    @bind_native("net/minecraft/world/effect/MobEffect", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name):
        this.registry_name = name
        return this

    @staticmethod
    @bind_native("net/minecraft/world/effect/MobEffect", "register()V")
    def registerMobEffect(method, stack, this):
        pass


class Particle:
    @staticmethod
    @bind_native("net/minecraft/core/particles/SimpleParticleType", "<init>(Z)V")
    def init(method, stack, this, flag):
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/core/particles/SimpleParticleType", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name: str):
        this.registry_name = name if ":" in name else shared.CURRENT_EVENT_SUB + ":" + name

    @staticmethod
    @bind_native("net/minecraft/core/particles/SimpleParticleType", "register()V")
    def register(method, stack, this):
        pass


class Rendering:
    @staticmethod
    @bind_native("net/minecraft/client/renderer/RenderType", "m_110457_()Lnet/minecraft/client/renderer/RenderType;")
    def cutoutMipped(method, stack):
        pass

    @staticmethod
    @bind_native("net/minecraft/client/renderer/RenderType", "m_110463_()Lnet/minecraft/client/renderer/RenderType;")
    def cutout(method, stack):
        pass

    @staticmethod
    @bind_native("net/minecraft/client/renderer/RenderType", "m_110466_()Lnet/minecraft/client/renderer/RenderType;")
    def translucent(method, stack):
        pass

    @staticmethod
    @bind_native("net/minecraft/client/renderer/ItemBlockRenderTypes", "setRenderLayer(Lnet/minecraft/world/level/block/Block;Lnet/minecraft/client/renderer/RenderType;)V")
    def setRenderLayer(method, stack, block, render_type):
        pass


class DamageSource:
    @staticmethod
    @bind_native("net/minecraft/util/DamageSource", "<init>(Ljava/lang/String;)V")
    def init(method, stack, this, name):
        pass

    @staticmethod
    @bind_native("net/minecraft/util/DamageSource", "func_76348_h()Lnet/minecraft/util/DamageSource;")
    def someFlag(method, stack, this):
        return this


class Network:
    @staticmethod
    @bind_native("net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder", "named(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder;")
    @bind_native("net/minecraftforge/network/NetworkRegistry$ChannelBuilder", "named(Lnet/minecraft/resources/ResourceLocation;)Lnet/minecraftforge/network/NetworkRegistry$ChannelBuilder;")
    @bind_native("net/minecraftforge/fmllegacy/network/NetworkRegistry$ChannelBuilder", "named(Lnet/minecraft/resources/ResourceLocation;)Lnet/minecraftforge/fmllegacy/network/NetworkRegistry$ChannelBuilder;")
    def createNamedChannel(method, stack, name):
        return method.cls.create_instance().init("()V")

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder", "<init>()V")
    @bind_native("net/minecraftforge/network/NetworkRegistry$ChannelBuilder", "<init>()V")
    def init(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder", "clientAcceptedVersions(Ljava/util/function/Predicate;)Lnet/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder;")
    @bind_native("net/minecraftforge/network/NetworkRegistry$ChannelBuilder", "clientAcceptedVersions(Ljava/util/function/Predicate;)Lnet/minecraftforge/network/NetworkRegistry$ChannelBuilder;")
    @bind_native("net/minecraftforge/fmllegacy/network/NetworkRegistry$ChannelBuilder", "clientAcceptedVersions(Ljava/util/function/Predicate;)Lnet/minecraftforge/fmllegacy/network/NetworkRegistry$ChannelBuilder;")
    def clientAcceptedVersions(method, stack, this, predicate):
        return this

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder", "serverAcceptedVersions(Ljava/util/function/Predicate;)Lnet/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder;")
    @bind_native("net/minecraftforge/network/NetworkRegistry$ChannelBuilder", "serverAcceptedVersions(Ljava/util/function/Predicate;)Lnet/minecraftforge/network/NetworkRegistry$ChannelBuilder;")
    @bind_native("net/minecraftforge/fmllegacy/network/NetworkRegistry$ChannelBuilder", "serverAcceptedVersions(Ljava/util/function/Predicate;)Lnet/minecraftforge/fmllegacy/network/NetworkRegistry$ChannelBuilder;")
    def serverAcceptedVersions(method, stack, this, predicate):
        return this

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder", "networkProtocolVersion(Ljava/util/function/Supplier;)Lnet/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder;")
    @bind_native("net/minecraftforge/network/NetworkRegistry$ChannelBuilder", "networkProtocolVersion(Ljava/util/function/Supplier;)Lnet/minecraftforge/network/NetworkRegistry$ChannelBuilder;")
    @bind_native("net/minecraftforge/fmllegacy/network/NetworkRegistry$ChannelBuilder", "networkProtocolVersion(Ljava/util/function/Supplier;)Lnet/minecraftforge/fmllegacy/network/NetworkRegistry$ChannelBuilder;")
    def networkProtocolVersion(method, stack, this, supplier):
        return this

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder", "simpleChannel()Lnet/minecraftforge/fml/network/simple/SimpleChannel;")
    @bind_native("net/minecraftforge/network/NetworkRegistry$ChannelBuilder", "simpleChannel()Lnet/minecraftforge/fml/network/simple/SimpleChannel;")
    @bind_native("net/minecraftforge/fmllegacy/network/NetworkRegistry$ChannelBuilder", "simpleChannel()Lnet/minecraftforge/fmllegacy/network/simple/SimpleChannel;")
    def simpleChannel(method, stack, this):
        return stack.vm.get_class("net/minecraftforge/fml/network/simple/SimpleChannel").create_instance().init("()V")

    @staticmethod
    @bind_native("net/minecraftforge/network/NetworkRegistry", "newSimpleChannel(Lnet/minecraft/resources/ResourceLocation;Ljava/util/function/Supplier;Ljava/util/function/Predicate;Ljava/util/function/Predicate;)Lnet/minecraftforge/network/simple/SimpleChannel;")
    def newSimpleChannel(method, stack, name, supplier, predicate_a, predicate_b):
        return stack.vm.get_class("net/minecraftforge/fml/network/simple/SimpleChannel").create_instance().init("()V")

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/simple/SimpleChannel", "<init>()V")
    def init(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/simple/SimpleChannel", "registerMessage(ILjava/lang/Class;Ljava/util/function/BiConsumer;Ljava/util/function/Function;Ljava/util/function/BiConsumer;)Lnet/minecraftforge/network/simple/IndexedMessageCodec$MessageHandler;")
    def registerMessage(method, stack, this, internal_id, cls, biconsumer_a, function, biconsumer_b):
        return stack.vm.get_class("net/minecraftforge/network/simple/IndexedMessageCodec$MessageHandler").create_instance()


class DeferredRegister:
    @staticmethod
    @bind_native("net/minecraftforge/registries/DeferredRegister", "create(Lnet/minecraftforge/registries/IForgeRegistry;Ljava/lang/String;)Lnet/minecraftforge/registries/DeferredRegister;")
    @bind_native("net/minecraftforge/registries/DeferredRegister", "create(Ljava/lang/Class;Ljava/lang/String;)Lnet/minecraftforge/registries/DeferredRegister;")
    def createDeferredRegister(method, stack, registry, mod_name: str):
        obj = method.cls.create_instance().init("()V")
        obj.mod_name = mod_name
        return obj

    @staticmethod
    @bind_native("net/minecraftforge/registries/DeferredRegister", "<init>()V")
    def init(method, stack, this):
        this.mod_name = "minecraft"

    @staticmethod
    @bind_native("net/minecraftforge/registries/DeferredRegister", "register(Ljava/lang/String;Ljava/util/function/Supplier;)Lnet/minecraftforge/fmllegacy/RegistryObject;")
    @bind_native("net/minecraftforge/registries/DeferredRegister", "register(Ljava/lang/String;Ljava/util/function/Supplier;)Lnet/minecraftforge/fml/RegistryObject;")
    @bind_native("net/minecraftforge/registries/DeferredRegister", "register(Ljava/lang/String;Ljava/util/function/Supplier;)Lnet/minecraftforge/registries/RegistryObject;")
    def register(method, stack, this, postfix_name: str, supplier):
        obj = supplier.invoke([])

        if obj is None:
            logger.println("Failed to register; object is null")
            return obj

        try:
            obj.get_method("setRegistryName", "(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;").invoke([obj, this.mod_name + ":" + postfix_name])
            obj.get_method("register", "()V").invoke([obj])
        except TypeError:
            breakpoint()
            raise

        return obj

    @staticmethod
    @bind_native("net/minecraftforge/registries/DeferredRegister", "register(Lnet/minecraftforge/eventbus/api/IEventBus;)V")
    def register(method, stack, this, event_bus):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/registries/ForgeRegistryEntry", "<init>()V")
    def init(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/registries/ForgeRegistryEntry", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name):
        this.registry_name = name
        return this

    @staticmethod
    @bind_native("net/minecraftforge/registries/ForgeRegistryEntry", "register()V")
    def register(method, stack, this):
        pass


class Codec:
    @staticmethod
    @bind_native("com/mojang/serialization/codecs/RecordCodecBuilder", "create(Ljava/util/function/Function;)Lcom/mojang/serialization/Codec;")
    def create(method, stack, function):
        return method.cls.create_instance().init("()V")

    @staticmethod
    @bind_native("com/mojang/serialization/codecs/RecordCodecBuilder", "<init>()V")
    def init(method, stack, this):
        pass

    @staticmethod
    @bind_native("com/mojang/serialization/codecs/RecordCodecBuilder", "register()V")
    def register(method, stack, this):
        pass

    @staticmethod
    @bind_native("com/mojang/serialization/Codec", "fieldOf(Ljava/lang/String;)Lcom/mojang/serialization/MapCodec;")
    def fieldOf(method, stack, this, name):
        return stack.vm.get_class("com/mojang/serialization/MapCodec").create_instance()

    @staticmethod
    @bind_native("com/mojang/serialization/MapCodec", "xmap(Ljava/util/function/Function;Ljava/util/function/Function;)Lcom/mojang/serialization/MapCodec;")
    def xmapForMapCodec(method, stack, this, function_a, function_b):
        return stack.vm.get_class("com/mojang/serialization/MapCodec").create_instance()

    @staticmethod
    @bind_native("com/mojang/serialization/MapCodec$MapCodecCodec", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name):
        this.registry_name = name
        return this

    @staticmethod
    @bind_native("com/mojang/serialization/MapCodec$MapCodecCodec", "register()V")
    def registerCodec(method, stack, this):
        pass

    @staticmethod
    @bind_native("com/mojang/serialization/MapCodec", "codec()Lcom/mojang/serialization/Codec;")
    def codecForMapCodec(method, stack, this):
        return stack.vm.get_class("com/mojang/serialization/MapCodec$MapCodecCodec").create_instance()

    @staticmethod
    @bind_native("com/mojang/serialization/Codec", "unit(Ljava/util/function/Supplier;)Lcom/mojang/serialization/Codec;")
    def unitForCodec(method, stack, supplier):
        return stack.vm.get_class("com/mojang/serialization/MapCodec$MapCodecCodec").create_instance()


class Properties:
    @staticmethod
    @bind_native("net/minecraft/world/level/block/state/properties/BooleanProperty", "m_61465_(Ljava/lang/String;)Lnet/minecraft/world/level/block/state/properties/BooleanProperty;")
    def createByName(method, stack, name: str):
        return method.get_class().create_instance()


class BiomeDictionary_Type:
    @staticmethod
    @bind_native("net/minecraftforge/common/BiomeDictionary$Type", "toString()Ljava/lang/String;")
    def toString(method, stack, this):
        return this.split("::")[-1]


class Tags:
    @staticmethod
    @bind_native("net/minecraft/tags/BlockTags", "createOptional(Lnet/minecraft/resources/ResourceLocation;)Lnet/minecraftforge/common/Tags$IOptionalNamedTag;")
    def createOptional(method, stack, name):
        name = name if isinstance(name, str) else name.name
        return stack.vm.get_class("net/minecraftforge/common/TagReference").create_instance().init("(H)V", "blocks", name)

    @staticmethod
    @bind_native("net/minecraft/tags/BlockTags", "m_13116_(Ljava/lang/String;)Lnet/minecraft/tags/Tag$Named;")
    def m_13116_(method, stack, name: str):  # todo: is this the correct thingy?
        return stack.vm.get_class("net/minecraftforge/common/TagReference").create_instance().init("(H)V", "blocks", name)

    @staticmethod
    @bind_native("net/minecraftforge/common/TagReference", "<init>(H)V")
    def init_tag_ref(method, stack, this, group: str, name: str):
        this.group = group
        this.name = name

    @staticmethod
    @bind_native("net/minecraft/tags/TagCollection", "m_7473_(Lnet/minecraft/tags/Tag;)Lnet/minecraft/resources/ResourceLocation;")
    def m_7473_(method, stack, this, tag):
        return stack.vm.get_class("net/minecraft/resources/ResourceLocation").create_instance().init("()V")


class LootModifier:
    @staticmethod
    @bind_native("net/minecraftforge/common/loot/GlobalLootModifierSerializer", "<init>()V")
    def init(method, stack, this):
        pass


class LootConditionalFunctions:
    @staticmethod
    @bind_native("net/minecraft/world/level/storage/loot/functions/LootItemConditionalFunction$Serializer", "<init>()V")
    def initSerializer(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/level/storage/loot/functions/LootItemFunctionType", "<init>(Lnet/minecraft/world/level/storage/loot/Serializer;)V")
    def initType(method, stack, this, serializer):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/level/storage/loot/functions/LootItemFunctionType", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name):
        this.registry_name = name
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/storage/loot/functions/LootItemFunctionType", "register()V")
    def register(method, stack, this):
        from mcpython.common.data.serializer.loot.LootTableFunction import ILootTableFunction

        @shared.registry
        class LootImplementation(ILootTableFunction):
            NAME = this.registry_name

            def apply(self, items: list, *args, **kwargs):
                pass  # todo: invoke here the underlying function somehow


class EntityBuilder:
    @staticmethod
    @bind_native("net/minecraft/world/level/block/entity/BlockEntityType$Builder", "m_155273_(Lnet/minecraft/world/level/block/entity/BlockEntityType$BlockEntitySupplier;[Lnet/minecraft/world/level/block/Block;)Lnet/minecraft/world/level/block/entity/BlockEntityType$Builder;")
    def create(method, stack, supplier, blocks):
        return method.get_class().create_instance()

    @staticmethod
    @bind_native("net/minecraft/world/level/block/entity/BlockEntityType$Builder", "m_58966_(Lcom/mojang/datafixers/types/Type;)Lnet/minecraft/world/level/block/entity/BlockEntityType;")
    def setDatafixerType(method, stack, instance, datafixer_type):
        return instance

    @staticmethod
    @bind_native("net/minecraft/world/level/block/entity/BlockEntityType$Builder", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name):
        this.registry_name = name
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/entity/BlockEntityType$Builder", "setRegistryName(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName2(method, stack, this, namespace, name):
        this.registry_name = namespace + ":" + name
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/entity/BlockEntityType$Builder", "setRegistryName(Lnet/minecraft/resources/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryNameFromResourceLoc(method, stack, this, name):
        this.registry_name = name.name
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/entity/BlockEntityType$Builder", "register()V")
    def register(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/entity/ai/attributes/AttributeModifier", "<init>(Ljava/util/UUID;Ljava/lang/String;DLnet/minecraft/world/entity/ai/attributes/AttributeModifier$Operation;)V")
    def initEntityAttributeModifier(method, stack, this, bind_uuid, string, double, operation):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/entity/EntityDimensions", "m_20395_(FF)Lnet/minecraft/world/entity/EntityDimensions;")
    @bind_native("net/minecraft/world/entity/EntityDimensions", "m_20398_(FF)Lnet/minecraft/world/entity/EntityDimensions;")
    def m_20395_(method, stack, a, b):
        return method.get_class().create_instance()

    @staticmethod
    @bind_native("net/minecraft/world/entity/EntityType$Builder", "m_20702_(I)Lnet/minecraft/world/entity/EntityType$Builder;")
    def m_20702_(method, stack, this, some_int):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/entity/EntityType$Builder", "m_20704_(Lnet/minecraft/world/entity/EntityType$EntityFactory;Lnet/minecraft/world/entity/MobCategory;)Lnet/minecraft/world/entity/EntityType$Builder;")
    def m_20704_(method, stack, factory, mob_category):
        return method.get_class().create_instance()

    @staticmethod
    @bind_native("net/minecraft/world/entity/EntityType$Builder", "setTrackingRange(I)Lnet/minecraft/world/entity/EntityType$Builder;")
    def setTrackingRange(method, stack, this, some_int):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/entity/EntityType$Builder", "setUpdateInterval(I)Lnet/minecraft/world/entity/EntityType$Builder;")
    def setUpdateInterval(method, stack, this, some_int):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/entity/EntityType$Builder", "m_20699_(FF)Lnet/minecraft/world/entity/EntityType$Builder;")
    def m_20699_(method, stack, this, float_a, float_b):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/entity/EntityType$Builder", "m_20712_(Ljava/lang/String;)Lnet/minecraft/world/entity/EntityType;")
    def build(method, stack, this, name):
        return stack.vm.get_class("net/minecraft/world/entity/EntityType").create_instance()

    @staticmethod
    @bind_native("net/minecraft/world/entity/EntityType", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name):
        this.registry_name = name
        return this

    @staticmethod
    @bind_native("net/minecraft/world/entity/EntityType", "register()V")
    def register(method, stack, this):
        pass


class MobSpawningSettings:
    @staticmethod
    @bind_native("net/minecraft/world/level/biome/MobSpawnSettings$SpawnerData", "<init>(Lnet/minecraft/world/entity/EntityType;III)V")
    def init(method, stack, this, entity_type, *ints):
        pass


class EntityRendering:
    @staticmethod
    @bind_native("net/minecraft/client/renderer/blockentity/BlockEntityRenderers", "m_173590_(Lnet/minecraft/world/level/block/entity/BlockEntityType;Lnet/minecraft/client/renderer/blockentity/BlockEntityRendererProvider;)V")
    def bindRenderer(method, stack, entity_type, renderer):
        pass


class Packages:
    @staticmethod
    @bind_native("net/minecraft/network/syncher/SynchedEntityData", "m_135353_(Ljava/lang/Class;Lnet/minecraft/network/syncher/EntityDataSerializer;)Lnet/minecraft/network/syncher/EntityDataAccessor;")
    def m_135353_(method, stack, cls, serializer):
        return method.get_class().create_instance()


class ReloadListener:
    @staticmethod
    @bind_native("net/minecraft/server/packs/resources/SimpleJsonResourceReloadListener", "<init>(Lcom/google/gson/Gson;Ljava/lang/String;)V")
    def initSimple(method, stack, this, gson_instance, name):
        pass


class TranslationTextComponent:
    @staticmethod
    @bind_native("net/minecraft/network/chat/TranslatableComponent", "<init>(Ljava/lang/String;)V")
    def init(method, stack, this, name: str):
        this.name = name

    @staticmethod
    @bind_native("net/minecraft/network/chat/TranslatableComponent", "add(Ljava/lang/Object;)Z")
    def add_trace(method, stack, this, obj):
        return True


class Direction:
    @staticmethod
    @bind_native("net/minecraft/core/Direction", "values()[Lnet/minecraft/core/Direction;")
    def valuesForDirection(method, stack):
        return EnumSide.iterate()


class Enchantment:
    @staticmethod
    @bind_native("net/minecraft/world/item/enchantment/Enchantment", "m_6586_()I")
    def getMaxLevel(method, stack, this):
        return 1

    class EnchantmentCategory:
        @staticmethod
        @bind_native("net/minecraft/world/item/enchantment/EnchantmentCategory", "values()[Lnet/minecraft/world/item/enchantment/EnchantmentCategory;")
        def values(method, stack):
            return []


class Vec3:
    @staticmethod
    @bind_native("net/minecraft/world/phys/Vec3", "<init>(DDD)V")
    def init(method, stack, this, a, b, c):
        this.underlying = a, b, c


class DataFixerUpper:
    @staticmethod
    @bind_native("com/mojang/datafixers/DSL", "emptyPartType()Lcom/mojang/datafixers/types/Type;")
    def emptyPartType(method, stack):
        return stack.vm.get_class("com/mojang/datafixers/types/Type").create_instance()


class ForgeMenuType:
    @staticmethod
    @bind_native("net/minecraftforge/common/extensions/IForgeMenuType", "create(Lnet/minecraftforge/network/IContainerFactory;)Lnet/minecraft/world/inventory/MenuType;")
    def createFromFactory(method, stack, factory):
        return stack.vm.get_class("net/minecraft/world/inventory/MenuType").create_instance()

    @staticmethod
    @bind_native("net/minecraft/world/inventory/MenuType", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name):
        this.registry_name = name

    @staticmethod
    @bind_native("net/minecraft/client/gui/screens/MenuScreens", "m_96206_(Lnet/minecraft/world/inventory/MenuType;Lnet/minecraft/client/gui/screens/MenuScreens$ScreenConstructor;)V")
    def m_96206_(method, stack, menu_type, screen_constructor):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/inventory/MenuType", "register()V")
    def register(method, stack, this):
        pass


class Commands:
    @staticmethod
    @bind_native("net/minecraft/commands/Commands", "m_82127_(Ljava/lang/String;)Lcom/mojang/brigadier/builder/LiteralArgumentBuilder;")
    def m_82127_(method, stack, some_string: str):
        return stack.vm.get_class("com/mojang/brigadier/builder/LiteralArgumentBuilder").create_instance()

    @staticmethod
    @bind_native("net/minecraft/commands/Commands", "m_82129_(Ljava/lang/String;Lcom/mojang/brigadier/arguments/ArgumentType;)Lcom/mojang/brigadier/builder/RequiredArgumentBuilder;")
    def m_82129_(method, stack, some_string: str, argument_type):
        return stack.vm.get_class("com/mojang/brigadier/builder/RequiredArgumentBuilder").create_instance()

    @staticmethod
    @bind_native("com/mojang/brigadier/builder/LiteralArgumentBuilder", "requires(Ljava/util/function/Predicate;)Lcom/mojang/brigadier/builder/ArgumentBuilder;")
    def requires(method, stack, this, predicate):
        return this

    @staticmethod
    @bind_native("com/mojang/brigadier/builder/LiteralArgumentBuilder", "executes(Lcom/mojang/brigadier/Command;)Lcom/mojang/brigadier/builder/ArgumentBuilder;")
    @bind_native("com/mojang/brigadier/builder/RequiredArgumentBuilder", "executes(Lcom/mojang/brigadier/Command;)Lcom/mojang/brigadier/builder/ArgumentBuilder;")
    def executes(method, stack, this, target):
        return this

    @staticmethod
    @bind_native("com/mojang/brigadier/builder/LiteralArgumentBuilder", "then(Lcom/mojang/brigadier/builder/ArgumentBuilder;)Lcom/mojang/brigadier/builder/ArgumentBuilder;")
    @bind_native("com/mojang/brigadier/builder/RequiredArgumentBuilder", "then(Lcom/mojang/brigadier/builder/ArgumentBuilder;)Lcom/mojang/brigadier/builder/ArgumentBuilder;")
    def then(method, stack, this, builder):
        return this

    @staticmethod
    @bind_native("com/mojang/brigadier/arguments/StringArgumentType", "word()Lcom/mojang/brigadier/arguments/StringArgumentType;")
    def word(method, stack):
        return method.get_class().create_instance()

    @staticmethod
    @bind_native("com/mojang/brigadier/arguments/BoolArgumentType", "bool()Lcom/mojang/brigadier/arguments/BoolArgumentType;")
    def boolType(method, stack):
        return method.get_class().create_instance()

    @staticmethod
    @bind_native("net/minecraftforge/event/RegisterCommandsEvent", "getDispatcher()Lcom/mojang/brigadier/CommandDispatcher;")
    def getDispatcher(method, stack, this):
        pass

    @staticmethod
    @bind_native("com/mojang/brigadier/CommandDispatcher", "register(Lcom/mojang/brigadier/builder/LiteralArgumentBuilder;)Lcom/mojang/brigadier/tree/LiteralCommandNode;")
    def registerCommand(method, stack, this, builder):
        return builder


class Recipes:
    @staticmethod
    @bind_native("net/minecraft/world/item/crafting/RecipeType", "m_44119_(Ljava/lang/String;)Lnet/minecraft/world/item/crafting/RecipeType;")
    def m_44119_(method, stack, some_string: str):
        obj = method.get_class().create_instance()
        obj.registry_name = some_string
        return obj

    @staticmethod
    @bind_native("net/minecraftforge/common/crafting/CraftingHelper", "register(Lnet/minecraft/resources/ResourceLocation;Lnet/minecraftforge/common/crafting/IIngredientSerializer;)Lnet/minecraftforge/common/crafting/IIngredientSerializer;")
    def registerIIngredientSerializer(method, stack, name, serializer):
        return serializer

    @staticmethod
    @bind_native("net/minecraftforge/common/crafting/CraftingHelper", "register(Lnet/minecraftforge/common/crafting/conditions/IConditionSerializer;)Lnet/minecraftforge/common/crafting/conditions/IConditionSerializer;")
    def registerIConditionSerializer(method, stack, serializer):
        return serializer


class TextureAtlas:
    @staticmethod
    @bind_native("net/minecraftforge/client/event/TextureStitchEvent$Pre", "getAtlas()Lnet/minecraft/client/renderer/texture/TextureAtlas;")
    @bind_native("net/minecraftforge/client/event/TextureStitchEvent$Post", "getAtlas()Lnet/minecraft/client/renderer/texture/TextureAtlas;")
    def getAtlas(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraft/client/renderer/texture/TextureAtlas", "m_118330_()Lnet/minecraft/resources/ResourceLocation;")
    def m_118330_(method, stack, this):
        pass


class WorldgenFeature:
    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/Feature", "<init>(Lcom/mojang/serialization/Codec;)V")
    def initFeature(method, stack, this, codec):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/Feature", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name):
        this.registry_name = name
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/Feature", "register()V")
    def register(method, stack, this):
        pass


class JigsawFeature:
    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/JigsawFeature", "<init>(Lcom/mojang/serialization/Codec;IZZLjava/util/function/Predicate;)V")
    def init(method, stack, this, codec, some_int, bool_a, bool_b, predicate):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/JigsawFeature", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name):
        this.registry_name = name
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/JigsawFeature", "getRegistryName()Lnet/minecraft/resources/ResourceLocation;")
    def getRegistryName(method, stack, this):
        return stack.vm.get_class(method.signature.split(")")[-1][1:-1]).create_instance().init("(Ljava/lang/String;)V", this.registry_name)

    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/JigsawFeature", "register()V")
    def register(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/JigsawFeature", "get()Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def get(method, stack, this):
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/configurations/JigsawConfiguration", "<init>(Ljava/util/function/Supplier;I)V")
    def init(method, stack, this, supplier, some_int):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/JigsawFeature", "m_67065_(Lnet/minecraft/world/level/levelgen/feature/configurations/FeatureConfiguration;)Lnet/minecraft/world/level/levelgen/feature/ConfiguredStructureFeature;")
    def m_67065_(method, stack, this, feature_config):
        return this


class StructureFeatureConfiguration:
    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/configurations/StructureFeatureConfiguration", "<init>(III)V")
    def init(method, stack, this, *ints):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/level/levelgen/feature/StructureFeature", "getRegistryName()Lnet/minecraft/resources/ResourceLocation;")
    def getRegistryName(method, stack, this):
        return stack.vm.get_class(method.signature.split(")")[-1][1:-1]).create_instance().init("(Ljava/lang/String;)V", this.registry_name)


class BlockPos:
    @staticmethod
    @bind_native("net/minecraft/core/BlockPos", "<init>(III)V")
    def init(method, stack, this, x, y, z):
        this.underlying = x, y, z


class CpwModLauncher:
    @staticmethod
    @bind_native("cpw/mods/modlauncher/Launcher", "environment()Lcpw/mods/modlauncher/Environment;")
    def getEnvironment(method, stack, this):
        return stack.vm.get_class("cpw/mods/modlauncher/Environment").create_instance()

    @staticmethod
    @bind_native("cpw/mods/modlauncher/Environment", "getProperty(Lcpw/mods/modlauncher/api/TypesafeMap$Key;)Ljava/util/Optional;")
    def getPropertyFromKey(method, stack, this, key):
        return key


jvm.api.vm.get_class("net/minecraft/world/item/CreativeModeTab").set_static_attribute("f_40748_", [])
jvm.api.vm.get_class("net/minecraftforge/registries/ForgeRegistries").set_static_attribute("ITEMS", lambda: shared.registry.get_by_name("minecraft:item"))
jvm.api.vm.get_class("net/minecraftforge/registries/ForgeRegistries").set_static_attribute("SOUND_EFFECTS", None)
jvm.api.vm.get_class("net/minecraft/world/level/levelgen/feature/StructureFeature").set_static_attribute("f_67012_", jvm.api.vm.get_class("com/google/common/collect/BiMap").create_instance().init("()V"))
jvm.api.vm.get_class("net/minecraft/world/level/levelgen/feature/StructureFeature").set_static_attribute("f_67031_", jvm.api.vm.get_class("java/util/List").create_instance().init("()V"))
jvm.api.vm.get_class("net/minecraft/world/level/levelgen/StructureSettings").set_static_attribute("f_64580_", jvm.api.vm.get_class("com/google/common/collect/ImmutableMap").create_instance().init("()V"))
jvm.api.vm.get_class("cpw/mods/modlauncher/api/IEnvironment$Keys").set_static_attribute("VERSION", lambda: "1.18")

