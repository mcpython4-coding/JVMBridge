import traceback
import typing

import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.JavaExceptionStack import StackCollectingException
from jvm.natives import bind_native, bind_annotation
from mcpython import shared
from mcpython.common.container.ResourceStack import ItemStack
from mcpython.common.mod.util import LoadingInterruptException
from mcpython.engine import logger

EVENT2STAGE: typing.Dict[str, str] = {
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/item/Item;>;)V": "stage:item:factory_usage",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/world/level/block/Block;>;)V": "stage:block:factory_usage",
    "(Lnet/minecraftforge/event/RegistryEvent$Register<Lnet/minecraft/block/Block;>;)V": "stage:block:factory_usage",
}


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
    def noAnnotationProcessing(method, stack, target, args):
        pass


def boundMethodToStage(method: AbstractMethod, event: str, mod: str):
    @shared.mod_loader(mod, event)
    def work():
        print(mod, event, method)
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
                raise LoadingInterruptException


class ModContainer:
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

            logger.println(f"[FML][WARN] mod {shared.CURRENT_EVENT_SUB} subscribed to event {signature} with {target}, but stage was not found")

    @staticmethod
    @bind_native("net/minecraftforge/eventbus/api/IEventBus", "addListener(Ljava/util/function/Consumer;)V")
    def addListener(method, stack, bus, listener):
        ModContainer.processEventAnnotation(method, stack, listener, [])

    @staticmethod
    @bind_native("net/minecraftforge/fml/DistExecutor", "runForDist(Ljava/util/function/Supplier;Ljava/util/function/Supplier;)Ljava/lang/Object;")
    def runForDist(method, stack, client, server):
        if shared.IS_CLIENT:
            client.invoke([])
        else:
            server.invoke([])

    @staticmethod
    @bind_native("net/minecraftforge/fml/javafmlmod/FMLJavaModLoadingContext", "get()Lnet/minecraftforge/fml/javafmlmod/FMLJavaModLoadingContext;")
    def getLoadingContext(method, stack):
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
    def register(method, stack, registry, name, obj):
        obj.get_method("register", "()V").invoke([obj])

    @staticmethod
    @bind_native("net/minecraftforge/fml/ModLoadingContext", "get()Lnet/minecraftforge/fml/ModLoadingContext;")
    def getContext(method, stack):
        return method.cls.create_instance()

    @staticmethod
    @bind_native("net/minecraftforge/fml/ModLoadingContext", "registerConfig(Lnet/minecraftforge/fml/config/ModConfig$Type;Lnet/minecraftforge/fml/config/IConfigSpec;Ljava/lang/String;)V")
    def registerConfig(method, stack, this, mod_config_type, config_spec, some_string: str):
        pass


class Configs:
    @staticmethod
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "<init>()V")
    def init(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "comment(Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "push(Ljava/lang/String;)Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "defineEnum(Ljava/lang/String;Ljava/lang/Enum;)Lnet/minecraftforge/common/ForgeConfigSpec$EnumValue;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "define(Ljava/lang/String;Z)Lnet/minecraftforge/common/ForgeConfigSpec$BooleanValue;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "pop()Lnet/minecraftforge/common/ForgeConfigSpec$Builder;")
    @bind_native("net/minecraftforge/common/ForgeConfigSpec$Builder", "build()Lnet/minecraftforge/common/ForgeConfigSpec;")
    def anyUnused(method, stack, this, *_):
        return this


class ItemCreation:
    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "<init>()V")
    def initProperties(method, stack, this):
        this.bound_tab = None
        this.rarity = -1

    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "m_41491_(Lnet/minecraft/world/item/CreativeModeTab;)Lnet/minecraft/world/item/Item$Properties;")
    def setItemTab(method, stack, this, tab):
        this.bound_tab = tab
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "m_41497_(Lnet/minecraft/world/item/Rarity;)Lnet/minecraft/world/item/Item$Properties;")
    def setRarity(method, stack, this, rarity):
        this.rarity = rarity  # todo: parse rarity for item
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item$Properties", "m_41487_(I)Lnet/minecraft/world/item/Item$Properties;")
    def setSomeInt(method, stack, this, value: int):
        return this  # todo: do something with value

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

    @staticmethod
    @bind_native("net/minecraft/world/item/BlockItem", "<init>(Lnet/minecraft/world/level/block/Block;Lnet/minecraft/world/item/Item$Properties;)V")
    def initBlockItem(method, stack, this, block, properties):
        this.properties = properties
        this.registry_name = None

    @staticmethod
    @bind_native("net/minecraft/world/item/Item", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/RecordItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/BoatItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/BucketItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/BlockItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name: str):
        this.registry_name = name if ":" in name else (shared.CURRENT_EVENT_SUB + ":" + name)
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item", "register()V")
    @bind_native("net/minecraft/world/item/RecordItem", "register()V")
    @bind_native("net/minecraft/world/item/BoatItem", "register()V")
    @bind_native("net/minecraft/world/item/BucketItem", "register()V")
    @bind_native("net/minecraft/world/item/BlockItem", "register()V")
    def register(method, stack, this):
        if this.get_class().name != "net/minecraft/world/item/BlockItem":
            from mcpython.common.factory.ItemFactory import ItemFactory

            instance = ItemFactory().set_name(this.registry_name)

            instance.finish()

        if this.properties.bound_tab is not None:
            @shared.mod_loader(shared.CURRENT_EVENT_SUB, "stage:item_groups:load")
            def bind_to_tab():
                try:
                    this.properties.bound_tab.instance.group.add(this.registry_name)
                except ValueError:
                    pass

    @staticmethod
    @bind_native("net/minecraft/item/ItemGroup", "<init>(Ljava/lang/String;)V")
    def init(method, stack, this, name):
        from mcpython.common.container.ItemGroup import ItemGroup
        this.underlying = ItemGroup()

    @staticmethod
    @bind_native("net/minecraft/world/item/CreativeModeTab", "<init>(ILjava/lang/String;)V")
    def initCreativeTab(method, stack, this, some_id, name: str):
        import mcpython.client.gui.InventoryCreativeTab

        tab = mcpython.client.gui.InventoryCreativeTab.CreativeItemTab(name, ItemStack("minecraft:barrier"))
        this.instance = tab

        mcpython.client.gui.InventoryCreativeTab.CT_MANAGER.add_tab(tab)


class BlockCreation:
    @staticmethod
    @bind_native("net/minecraft/world/level/block/Block", "m_49796_(DDDDDD)Lnet/minecraft/world/phys/shapes/VoxelShape;")
    def createVoxelShape(method, stack, *some_values):
        pass

    @staticmethod
    @bind_native("net/minecraft/world/phys/shapes/Shapes", "m_83110_(Lnet/minecraft/world/phys/shapes/VoxelShape;Lnet/minecraft/world/phys/shapes/VoxelShape;)Lnet/minecraft/world/phys/shapes/VoxelShape;")
    def combine(method, stack, a, b):
        return a

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
    def setSomeFlag(method, stack, this, *value):
        return this

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
    def initBlock(method, stack, this, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False

    @staticmethod
    @bind_native("net/minecraft/world/level/block/PressurePlateBlock", "<init>(Lnet/minecraft/world/level/block/PressurePlateBlock$Sensitivity;Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initPressurePlate(method, stack, this, sensitivity, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False

    @staticmethod
    @bind_native("net/minecraft/world/level/block/LiquidBlock", "<init>(Ljava/util/function/Supplier;Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initLiquidBlock(method, stack, this, liquid_supplier, properties):
        this.liquid_supplier = liquid_supplier
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False

    @staticmethod
    @bind_native("net/minecraft/world/level/block/SandBlock", "<init>(ILnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initSandBlock(method, stack, this, some_int, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = True
        this.is_slab = False
        this.is_log = False

    @staticmethod
    @bind_native("net/minecraft/world/level/block/StairBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockState;Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initStairBlock(method, stack, this, state, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False

    @staticmethod
    @bind_native("net/minecraft/world/level/block/SlabBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initSlabBlock(method, stack, this, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = True
        this.is_log = False

    @staticmethod
    @bind_native("net/minecraft/world/level/block/Blocks", "m_50788_(Lnet/minecraft/world/level/material/MaterialColor;Lnet/minecraft/world/level/material/MaterialColor;)Lnet/minecraft/world/level/block/RotatedPillarBlock;")
    def createLog(method, stack, material_color_1, material_color_2):
        properties = stack.vm.get_class("net/minecraft/world/level/block/state/BlockBehaviour$Properties").create_instance().init("()V")
        instance = stack.vm.get_class("net/minecraft/world/level/block/RotatedPillarBlock").create_instance().init("(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V", properties)
        properties.is_log = True
        return instance

    @staticmethod
    @bind_native("net/minecraft/world/level/block/SaplingBlock", "<init>(Lnet/minecraft/world/level/block/grower/AbstractTreeGrower;Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initSaplingBlock(method, stack, this, tree_grower, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False

    @staticmethod
    @bind_native("net/minecraft/world/level/block/FlowerBlock", "<init>(Lnet/minecraft/world/effect/MobEffect;ILnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initFlowerBlock(method, stack, this, effect, some_int, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False

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

    @staticmethod
    @bind_native("net/minecraft/world/level/block/PipeBlock", "<init>(FLnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initGrowingPlantHeadBlock(method, stack, this, some_float, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False

    @staticmethod
    @bind_native("net/minecraft/world/level/block/MushroomBlock", "<init>(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;Ljava/util/function/Supplier;)V")
    def initMushroomBlock(method, stack, this, properties, supplier):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False

    @staticmethod
    @bind_native("net/minecraft/world/level/block/AmethystClusterBlock", "<init>(IILnet/minecraft/world/level/block/state/BlockBehaviour$Properties;)V")
    def initAmethystClusterBlock(method, stack, this, a, b, properties):
        this.properties = properties
        this.registry_name = None
        this.is_falling = False
        this.is_slab = False
        this.is_log = False

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
    def setRegistryName(method, stack, this, name):
        this.registry_name = name if ":" in name else shared.CURRENT_EVENT_SUB + ":" + name
        return this

    @staticmethod
    @bind_native("net/minecraft/world/level/block/Block", "m_49966_()Lnet/minecraft/world/level/block/state/BlockState;")
    def getDefaultBlockState(method, stack, this):
        pass

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

        if this.properties is not None:
            try:
                if this.properties.is_log:
                    factory.set_log()
            except AttributeError:
                pass

            factory.set_strength(*this.properties.hardness)

        factory.finish()

    @staticmethod
    @bind_native("net/minecraft/world/level/block/LiquidBlock", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    @bind_native("net/minecraft/world/level/block/SaplingBlock", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    @bind_native("net/minecraft/world/level/block/HorizontalDirectionalBlock", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    @bind_native("net/minecraft/world/level/block/DoublePlantBlock", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    @bind_native("net/minecraft/world/level/block/Block", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    @bind_native("net/minecraft/world/level/block/PipeBlock", "m_49959_(Lnet/minecraft/world/level/block/state/BlockState;)V")
    def registerDefaultState(method, stack, this, state):
        pass

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


class ForgeRegistries:
    @staticmethod
    @bind_native("net/minecraftforge/registries/IForgeRegistry", "register(Lnet/minecraftforge/registries/IForgeRegistryEntry;)V")
    def register(method, stack, this, obj):
        obj.get_method("register", "()V").invoke([obj], stack=stack)

    @staticmethod
    @bind_native("net/minecraftforge/fmllegacy/RegistryObject", "of(Lnet/minecraft/resources/ResourceLocation;Lnet/minecraftforge/registries/IForgeRegistry;)Lnet/minecraftforge/fmllegacy/RegistryObject;")
    def getObjectByName(method, stack, name, registry):
        if registry is None:
            return method.cls.create_instance()

        raise RuntimeError


class ResourceLocation:
    @staticmethod
    @bind_native("net/minecraft/resources/ResourceLocation", "<init>(Ljava/lang/String;Ljava/lang/String;)V")
    @bind_native("net/minecraft/util/ResourceLocation", "<init>(Ljava/lang/String;Ljava/lang/String;)V")
    def init(method, stack, this, namespace, name):
        try:
            this.name = namespace + ":" + name
        except TypeError:
            breakpoint()
            raise

    @staticmethod
    @bind_native("net/minecraft/util/ResourceLocation", "<init>(Ljava/lang/String;)V")
    @bind_native("net/minecraft/resources/ResourceLocation", "<init>(Ljava/lang/String;)V")
    def init(method, stack, this, name):
        this.name = name if ":" in name else shared.CURRENT_EVENT_SUB + ":" + name


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
    @bind_native("net/minecraft/world/effect/MobEffect", "m_8093_()Z")
    def isInstantenous(method, stack, this):
        return True


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
    def createNamedChannel(method, stack, name):
        return method.cls.create_instance().init("()V")

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder", "<init>()V")
    def init(method, stack, this):
        pass

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder", "clientAcceptedVersions(Ljava/util/function/Predicate;)Lnet/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder;")
    def clientAcceptedVersions(method, stack, this, predicate):
        return this

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder", "serverAcceptedVersions(Ljava/util/function/Predicate;)Lnet/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder;")
    def serverAcceptedVersions(method, stack, this, predicate):
        return this

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder", "networkProtocolVersion(Ljava/util/function/Supplier;)Lnet/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder;")
    def networkProtocolVersion(method, stack, this, supplier):
        return this

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/NetworkRegistry$ChannelBuilder", "simpleChannel()Lnet/minecraftforge/fml/network/simple/SimpleChannel;")
    def simpleChannel(method, stack, this):
        return stack.vm.get_class("net/minecraftforge/fml/network/simple/SimpleChannel").create_instance().init("()V")

    @staticmethod
    @bind_native("net/minecraftforge/fml/network/simple/SimpleChannel", "<init>()V")
    def init(method, stack, this):
        pass


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
    def register(method, stack, this, postfix_name: str, supplier):
        obj = supplier.invoke([])
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


jvm.api.vm.get_class("net/minecraft/world/item/CreativeModeTab").set_static_attribute("f_40748_", [])
jvm.api.vm.get_class("net/minecraftforge/registries/ForgeRegistries").set_static_attribute("ITEMS", lambda: shared.registry.get_by_name("minecraft:item"))
jvm.api.vm.get_class("net/minecraftforge/registries/ForgeRegistries").set_static_attribute("SOUND_EFFECTS", None)

