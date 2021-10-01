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

EVENT2STAGE: typing.Dict[typing.Union[str, typing.Tuple[str, str]], str] = {
    ("Lnet/minecraftforge/event/RegistryEvent$Register;", "registerItems"): "stage:item:factory_usage",
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
    def noAnnotationProcessing(method, stack, target, args):
        pass


def boundMethodToStage(method: AbstractMethod, event: str, mod: str):
    @shared.mod_loader(mod, event)
    def work():
        shared.CURRENT_EVENT_SUB = mod
        try:
            method.invoke([] if method.access & 0x0008 else [None])
        except StackCollectingException as e:
            if shared.IS_CLIENT:
                traceback.print_exc()
                print(e.format_exception())
                e.method_call_stack[0].code_repr.print_stats()

                import mcpython.common.state.LoadingExceptionViewState
                mcpython.common.state.LoadingExceptionViewState.error_occur(e.format_exception())
                raise LoadingInterruptException from None

            else:
                raise LoadingInterruptException


class ModContainer:
    @staticmethod
    @bind_annotation("net/minecraftforge/fml/common/Mod")
    def processModAnnotation(method, stack, target, args):
        pass

    @staticmethod
    @bind_annotation("net/minecraftforge/fml/common/Mod$EventHandler")
    @bind_annotation("net/minecraftforge/fml/common/Mod$EventBusSubscriber")
    @bind_annotation("net/minecraftforge/fml/common/eventhandler/SubscribeEvent")
    @bind_annotation("net/minecraftforge/eventbus/api/SubscribeEvent")
    def processEventAnnotation(method, stack, target, args):
        if isinstance(target, AbstractMethod):
            event_name = target.signature.split(")")[0].removeprefix("(")

            if event_name in EVENT2STAGE and EVENT2STAGE[event_name]:
                boundMethodToStage(target, EVENT2STAGE[event_name], shared.CURRENT_EVENT_SUB)
                return
            if (event_name, target.name) in EVENT2STAGE:
                stage = EVENT2STAGE[(event_name, target.name)]
                if stage is not None:
                    boundMethodToStage(target, stage, shared.CURRENT_EVENT_SUB)
                    return

            logger.println(f"[FML][WARN] mod {shared.CURRENT_EVENT_SUB} subscribed to event {event_name} with {target}, but stage was not found")


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
    @bind_native("net/minecraft/world/item/Item", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/RecordItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/BoatItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    @bind_native("net/minecraft/world/item/BucketItem", "setRegistryName(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;")
    def setRegistryName(method, stack, this, name: str):
        this.registry_name = name if ":" in name else (shared.CURRENT_EVENT_SUB + ":" + name)
        return this

    @staticmethod
    @bind_native("net/minecraft/world/item/Item", "register()V")
    @bind_native("net/minecraft/world/item/RecordItem", "register()V")
    @bind_native("net/minecraft/world/item/BoatItem", "register()V")
    @bind_native("net/minecraft/world/item/BucketItem", "register()V")
    def register(method, stack, this):
        from mcpython.common.factory.ItemFactory import ItemFactory

        instance = ItemFactory().set_name(this.registry_name)

        instance.finish()

        if this.properties.bound_tab is not None:
            this.properties.bound_tab.instance.group.add(this.registry_name)

    @staticmethod
    @bind_native("net/minecraft/world/item/CreativeModeTab", "<init>(ILjava/lang/String;)V")
    def initCreativeTab(method, stack, this, some_id, name: str):
        import mcpython.client.gui.InventoryCreativeTab

        tab = mcpython.client.gui.InventoryCreativeTab.CreativeItemTab(name, ItemStack("minecraft:barrier"))
        this.instance = tab

        mcpython.client.gui.InventoryCreativeTab.CT_MANAGER.add_tab(tab)


class ForgeRegistries:
    @staticmethod
    @bind_native("net/minecraftforge/registries/IForgeRegistry", "register(Lnet/minecraftforge/registries/IForgeRegistryEntry;)V")
    def register(method, stack, this, obj):
        obj.get_method("register", "()V").invoke([obj], stack=stack)

    @staticmethod
    @bind_native("net/minecraftforge/fmllegacy/RegistryObject", "of(Lnet/minecraft/resources/ResourceLocation;Lnet/minecraftforge/registries/IForgeRegistry;)Lnet/minecraftforge/fmllegacy/RegistryObject;")
    def getObjectByName(method, stack, name, registry):
        if registry is None: return
        raise RuntimeError


class ResourceLocation:
    @staticmethod
    @bind_native("net/minecraft/resources/ResourceLocation", "<init>(Ljava/lang/String;Ljava/lang/String;)V")
    def init(method, stack, this, namespace, name):
        this.name = namespace + ":" + name


jvm.api.vm.get_class("net/minecraft/world/item/CreativeModeTab").set_static_attribute("f_40748_", [])
jvm.api.vm.get_class("net/minecraftforge/registries/ForgeRegistries").set_static_attribute("ITEMS", lambda: shared.registry.get_by_name("minecraft:item"))
jvm.api.vm.get_class("net/minecraftforge/registries/ForgeRegistries").set_static_attribute("SOUND_EFFECTS", None)

