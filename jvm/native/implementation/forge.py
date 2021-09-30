import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.natives import bind_native, bind_annotation


class Annotations:
    @staticmethod
    @bind_annotation("net/minecraftforge/fml/relauncher/IFMLLoadingPlugin$Name")
    @bind_annotation("net/minecraftforge/fml/relauncher/IFMLLoadingPlugin$MCVersion")
    @bind_annotation("net/minecraftforge/fml/relauncher/IFMLLoadingPlugin$TransformerExclusions")
    @bind_annotation("net/minecraftforge/fml/relauncher/IFMLLoadingPlugin$SortingIndex")
    @bind_annotation("net/minecraftforge/fml/relauncher/SideOnly")
    @bind_annotation("mcp/MethodsReturnNonnullByDefault")
    @bind_annotation("net/minecraftforge/fml/common/Optional$Method")
    @bind_annotation("net/minecraftforge/fml/common/Optional$Interface")
    @bind_annotation("net/minecraftforge/common/config/Config")
    def noAnnotationProcessing(method, stack, target, args):
        pass


class ModContainer:
    @staticmethod
    @bind_annotation("net/minecraftforge/fml/common/Mod")
    def processModAnnotation(method, stack, target, args):
        pass

    @staticmethod
    @bind_annotation("net/minecraftforge/fml/common/Mod$EventHandler")
    @bind_annotation("net/minecraftforge/fml/common/Mod$EventBusSubscriber")
    @bind_annotation("net/minecraftforge/fml/common/eventhandler/SubscribeEvent")
    def processEventAnnotation(method, stack, target, args):
        pass

