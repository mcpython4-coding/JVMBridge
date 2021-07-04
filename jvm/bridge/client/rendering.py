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


class RenderType(NativeClass):
    NAME = "net/minecraft/client/renderer/RenderType"

    @native("func_228641_d_", "()Lnet/minecraft/client/renderer/RenderType;")
    def func_228641_d_(self):
        pass

    @native("func_228643_e_", "()Lnet/minecraft/client/renderer/RenderType;")
    def func_228643_e_(self):
        pass

    @native("func_228645_f_", "()Lnet/minecraft/client/renderer/RenderType;")
    def func_228645_f_(self):
        pass


class RenderTypeLookup(NativeClass):
    NAME = "net/minecraft/client/renderer/RenderTypeLookup"

    @native(
        "setRenderLayer",
        "(Lnet/minecraft/block/Block;Lnet/minecraft/client/renderer/RenderType;)V",
    )
    def setRenderLayer(self, block, render_type):
        pass


class ModelProperty(NativeClass):
    NAME = "net/minecraftforge/client/model/data/ModelProperty"

    @native("<init>", "()V")
    def init(self, *_):
        pass

    @native("<init>", "(Ljava/util/function/Predicate;)V")
    def init2(self, *_):
        pass


class ParticleType(NativeClass):
    NAME = "net/minecraft/particles/ParticleType"

    @native("<init>", "(ZLnet/minecraft/particles/IParticleData$IDeserializer;)V")
    def init(self, instance, v, deserializer):
        pass


class RedstoneParticleData(NativeClass):
    NAME = "net/minecraft/particles/RedstoneParticleData"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "field_197564_a": None,
        })


class BlockColors(NativeClass):
    NAME = "net/minecraft/client/renderer/color/BlockColors"

    @native(
        "func_186722_a",
        "(Lnet/minecraft/client/renderer/color/IBlockColor;[Lnet/minecraft/block/Block;)V",
    )
    def func_186722_a(self, instance, color, blocks):
        pass


class EndPortalTileEntityRenderer(NativeClass):
    NAME = "net/minecraft/client/renderer/tileentity/EndPortalTileEntityRenderer"


class SoundEngine(NativeClass):
    NAME = "net/minecraft/client/audio/SoundEngine"


class WorldRenderer(NativeClass):
    NAME = "net/minecraft/client/renderer/WorldRenderer"


class FirstPersonRenderer(NativeClass):
    NAME = "net/minecraft/client/renderer/FirstPersonRenderer"

    @native("func_228406_b_", "(Lcom/mojang/blaze3d/matrix/MatrixStack;Lnet/minecraft/util/HandSide;F)V")
    def func_228406_b_(self, *_):
        pass

    @native("func_228399_a_", "(Lcom/mojang/blaze3d/matrix/MatrixStack;Lnet/minecraft/util/HandSide;F)V")
    def func_228399_a_(self, *_):
        pass


class RenderTypeBuffers(NativeClass):
    NAME = "net/minecraft/client/renderer/RenderTypeBuffers"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "field_228480_b_": None
        })


class SkullTileEntityRenderer(NativeClass):
    NAME = "net/minecraft/client/renderer/tileentity/SkullTileEntityRenderer"

    @native("func_228878_a_",
            "(Lnet/minecraft/block/SkullBlock$ISkullType;Lcom/mojang/authlib/GameProfile;)Lnet/minecraft/client/renderer/RenderType;")
    def func_228878_a_(self, *_):
        pass


class ItemOverrideList(NativeClass):
    NAME = "net/minecraft/client/renderer/model/ItemOverrideList"


class ModelBakery(NativeClass):
    NAME = "net/minecraft/client/renderer/model/ModelBakery"


class RenderState(NativeClass):
    NAME = "net/minecraft/client/renderer/RenderState"


class ResourceLoadProgressGui(NativeClass):
    NAME = "net/minecraft/client/gui/ResourceLoadProgressGui"


class DimensionRenderInfo(NativeClass):
    NAME = "net/minecraft/client/world/DimensionRenderInfo"


class BakedQuad(NativeClass):
    NAME = "net/minecraft/client/renderer/model/BakedQuad"


class BlockModel(NativeClass):
    NAME = "net/minecraft/client/renderer/model/BlockModel"


class BlockPartFace__Deserializer(NativeClass):
    NAME = "net/minecraft/client/renderer/model/BlockPartFace$Deserializer"


class LanguageManager(NativeClass):
    NAME = "net/minecraft/client/resources/LanguageManager"


class AndCondition(NativeClass):
    NAME = "net/minecraft/client/renderer/model/multipart/AndCondition"


class OrCondition(NativeClass):
    NAME = "net/minecraft/client/renderer/model/multipart/OrCondition"


class ModelResourceLocation(NativeClass):
    NAME = "net/minecraft/client/renderer/model/ModelResourceLocation"


class MultipartBakedModel__Builder(NativeClass):
    NAME = "net/minecraft/client/renderer/model/MultipartBakedModel$Builder"


class SimpleBakedModel__Builder(NativeClass):
    NAME = "net/minecraft/client/renderer/model/SimpleBakedModel$Builder"


class PropertyValueCondition(NativeClass):
    NAME = "net/minecraft/client/renderer/model/multipart/PropertyValueCondition"


class GameRenderer(NativeClass):
    NAME = "net/minecraft/client/renderer/GameRenderer"


class DebugOverlayGui(NativeClass):
    NAME = "net/minecraft/client/gui/overlay/DebugOverlayGui"


class CapeLayer(NativeClass):
    NAME = "net/minecraft/client/renderer/entity/layers/CapeLayer"


class RenderSkyboxCube(NativeClass):
    NAME = "net/minecraft/client/renderer/RenderSkyboxCube"


class Debug__Renderer(NativeClass):
    NAME = "org/jetbrains/annotations/Debug$Renderer"


class EditStructureScreen(NativeClass):
    NAME = "net/minecraft/client/gui/screen/EditStructureScreen"
