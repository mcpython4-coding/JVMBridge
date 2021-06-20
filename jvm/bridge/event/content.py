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
import mcpython.common.container.ResourceStack
from mcpython import shared
from jvm.Java import NativeClass, native
from jvm.JavaExceptionStack import StackCollectingException


class Blocks(NativeClass):
    NAME = "net/minecraft/block/Blocks"

    def __init__(self):
        super().__init__()

    def get_static_attribute(self, name: str, expected_type=None):
        if name in self.exposed_attributes:
            return self.exposed_attributes[name]
        return None  # todo: registry lookup when needed

    @native(
        "func_235430_a_",
        "(Lnet/minecraft/block/material/MaterialColor;Lnet/minecraft/block/material/MaterialColor;)Lnet/minecraft/block/RotatedPillarBlock;",
    )
    def func_235430_a_(self, color_a, color_b):
        # todo: this seems odd
        instance = self.vm.get_class(
            "net/minecraft/block/RotatedPillarBlock", version=self.internal_version
        ).create_instance()
        instance.properties = self.vm.get_class(
            "net/minecraft/block/AbstractBlock$Properties",
            version=self.internal_version,
        ).create_instance()
        return instance


class AbstractBlock(NativeClass):
    NAME = "net/minecraft/block/AbstractBlock"


class AbstractBlock_Properties(NativeClass):
    NAME = "net/minecraft/block/AbstractBlock$Properties"

    def create_instance(self):
        instance = super().create_instance()
        instance.hardness = instance.blast_resistance = 0
        instance.harvest_level = 0
        instance.harvest_tool = 0
        return instance

    @native(
        "func_200949_a",
        "(Lnet/minecraft/block/material/Material;Lnet/minecraft/block/material/MaterialColor;)Lnet/minecraft/block/AbstractBlock$Properties;",
    )
    def func_200949_a(self, material, material_color):
        return self.create_instance()

    @native("func_200943_b", "(F)Lnet/minecraft/block/AbstractBlock$Properties;")
    def func_200943_b(self, instance, value):
        if not isinstance(value, float):
            raise StackCollectingException("invalid data type")

        instance.hardness = instance.blast_resistance = value
        return instance

    @native(
        "func_200947_a",
        "(Lnet/minecraft/block/SoundType;)Lnet/minecraft/block/AbstractBlock$Properties;",
    )
    def setSoundType(self, instance, sound_type):
        return instance

    @native("harvestLevel", "(I)Lnet/minecraft/block/AbstractBlock$Properties;")
    def harvestLevel(self, instance, level: int):
        instance.harvest_level = level
        return instance

    @native(
        "harvestTool",
        "(Lnet/minecraftforge/common/ToolType;)Lnet/minecraft/block/AbstractBlock$Properties;",
    )
    def harvestTool(self, instance, tool):
        # todo: inject into TAG
        instance.harvest_tool = tool
        return instance

    @native(
        "func_200950",
        "(Lnet/minecraft/block/AbstractBlock;)Lnet/minecraft/block/AbstractBlock$Properties;",
    )
    def func_200950(self, instance, a):
        return instance

    @native(
        "func_200950_a",
        "(Lnet/minecraft/block/AbstractBlock;)Lnet/minecraft/block/AbstractBlock$Properties;",
    )
    def func_200950_a(self, instance):
        return instance.properties if instance is not None else None

    @native("func_200948_a", "(FF)Lnet/minecraft/block/AbstractBlock$Properties;")
    def func_200948_a(self, instance, a, b):
        instance.hardness, instance.blast_resistance = a, b
        return instance

    @native(
        "func_200945_a",
        "(Lnet/minecraft/block/material/Material;)Lnet/minecraft/block/AbstractBlock$Properties;",
    )
    def func_200945_a(self, material):
        return self.create_instance()

    @native("func_200944_c", "()Lnet/minecraft/block/AbstractBlock$Properties;")
    def func_200944_c(self, instance):
        return instance

    @native(
        "func_235838_a_",
        "(Ljava/util/function/ToIntFunction;)Lnet/minecraft/block/AbstractBlock$Properties;",
    )
    def func_235838_a_(self, instance, method):
        return instance

    @native("func_200942_a", "()Lnet/minecraft/block/AbstractBlock$Properties;")
    def func_200942_a(self, instance):
        return instance

    @native("func_200946_b", "()Lnet/minecraft/block/AbstractBlock$Properties;")
    def func_200946_b(self, instance):
        return instance

    @native("func_226896_b_", "()Lnet/minecraft/block/AbstractBlock$Properties;")
    def func_226896_b_(self, instance):
        return instance

    @native("func_180632_j", "(Lnet/minecraft/block/BlockState;)V")
    def func_180632_j(self, instance, value, blockstate):
        pass

    @native(
        "func_235842_b_",
        "(Lnet/minecraft/block/AbstractBlock$IPositionPredicate;)Lnet/minecraft/block/AbstractBlock$Properties;",
    )
    def func_235842_b_(self, instance, position_predicate):
        return instance

    @native(
        "func_235828_a_",
        "(Lnet/minecraft/block/AbstractBlock$IPositionPredicate;)Lnet/minecraft/block/AbstractBlock$Properties;",
    )
    def func_235828_a_(self, instance, position_predicate):
        return instance

    @native("func_235861_h_", "()Lnet/minecraft/block/AbstractBlock$Properties;")
    def func_235861_h_(self, instance):
        return instance

    @native(
        "func_235827_a_",
        "(Lnet/minecraft/block/AbstractBlock$IExtendedPositionPredicate;)Lnet/minecraft/block/AbstractBlock$Properties;",
    )
    def func_235827_a_(self, instance, predicate):
        return instance

    @native(
        "func_206870_a",
        "(Lnet/minecraft/state/Property;Ljava/lang/Comparable;)Ljava/lang/Object;",
    )
    def func_206870_a(self, instance, prop, value):
        pass

    @native("func_222380_e", "()Lnet/minecraft/block/AbstractBlock$Properties;")
    def func_222380_e(self, instance):
        return instance

    @native("func_235847_c_",
            "(Lnet/minecraft/block/AbstractBlock$IPositionPredicate;)Lnet/minecraft/block/AbstractBlock$Properties;")
    def func_235847_c_(self, instance, predicate):
        return instance


class SoundType(NativeClass):
    NAME = "net/minecraft/block/SoundType"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_185855_h": None,
                "field_185850_c": None,
                "field_185848_a": None,
                "field_185851_d": None,
                "field_185853_f": None,
                "field_185849_b": None,
                "field_185852_e": None,
            }
        )

    @native(
        "<init>",
        "(FFLnet/minecraft/util/SoundEvent;Lnet/minecraft/util/SoundEvent;Lnet/minecraft/util/SoundEvent;Lnet/minecraft/util/SoundEvent;Lnet/minecraft/util/SoundEvent;)V",
    )
    def init(self, instance, a, b, c, d, e, f, g):
        pass


class SoundEvents(NativeClass):
    NAME = "net/minecraft/util/SoundEvents"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_187872_fl": None,
                "field_187888_ft": None,
                "field_187884_fr": None,
                "field_187878_fo": None,
                "field_187876_fn": None,
                "field_187581_bW": None,
                "field_187668_ca": None,
                "field_187587_bZ": None,
                "field_187585_bY": None,
                "field_187583_bX": None,
                "field_211419_ds": None,
                "field_211423_dw": None,
                "field_211422_dv": None,
                "field_211421_du": None,
                "field_211420_dt": None,
                "field_187561_bM": None,
                "field_187569_bQ": None,
                "field_187567_bP": None,
                "field_187565_bO": None,
                "field_187563_bN": None,
            }
        )


class ToolType(NativeClass):
    NAME = "net/minecraftforge/common/ToolType"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "SHOVEL": "net/minecraft/block/ToolType::SHOVEL",
                "PICKAXE": "net/minecraft/block/ToolType::PICKAXE",
                "AXE": "net/minecraft/block/ToolType::AXE",
                "WRENCH": "net/minecraft/block/ToolType::WRENCH",
                "HOE": "net/minecraft/block/ToolType::HOE",
            }
        )

    @native("get", "(Ljava/lang/String;)Lnet/minecraftforge/common/ToolType;")
    def get(self, text: str):
        return self.exposed_attributes[text.upper()]


class Block(AbstractBlock):
    NAME = "net/minecraft/block/Block"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties

    @native("func_176223_P", "()Lnet/minecraft/block/BlockState;")
    def func_176223_P(self, instance):
        return instance.properties if instance is not None else None

    @native(
        "setRegistryName",
        "(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, name: str):
        instance.registry_name = name
        return instance

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName2(self, instance, namespace: str, name: str):
        if instance is None:
            return instance

        instance.registry_name = namespace + ":" + name
        return instance

    @native(
        "setRegistryName",
        "(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName3(self, instance, name):
        return instance

    @native("getRegistryName", "()Lnet/minecraft/util/ResourceLocation;")
    def getRegistryName(self, instance):
        return instance.registry_name if instance is not None else None

    @native("func_208617_a", "(DDDDDD)Lnet/minecraft/util/math/shapes/VoxelShape;")
    def func_208617_a(self, *v):
        pass

    @native("func_235697_s_", "()Lnet/minecraft/block/material/MaterialColor;")
    def getMaterialColor(self, instance):
        pass

    @native("func_180632_j", "(Lnet/minecraft/block/BlockState;)V")
    def func_180632_j(self, instance, state):
        pass

    def get_dynamic_field_keys(self):
        return super().get_dynamic_field_keys() | {"field_176227_L"}


class Material(NativeClass):
    NAME = "net/minecraft/block/material/Material"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_151595_p": None,
                "field_151576_e": None,
                "field_151578_c": None,
                "field_151577_b": None,
                "field_151583_m": None,
                "field_151592_s": None,
                "field_151575_d": None,
                "field_151585_k": None,
                "field_151584_j": None,
                "field_151594_q": None,
                "field_151582_l": None,
                "field_204868_h": None,
                "field_203243_f": None,
                "field_151573_f": None,
                "field_151586_h": None,
                "field_151572_C": None,
            }
        )

    @native("func_151565_r", "()Lnet/minecraft/block/material/MaterialColor;")
    def getMaterialColor(self, instance):
        pass

    @native(
        "<init>",
        "(Lnet/minecraft/block/material/MaterialColor;ZZZZZZLnet/minecraft/block/material/PushReaction;)V",
    )
    def init(self, instance, color, a, b, c, d, e, f, reaction):
        pass


class Material__Builder(NativeClass):
    NAME = "net/minecraft/block/material/Material$Builder"

    @native("<init>", "(Lnet/minecraft/block/material/MaterialColor;)V")
    def init(self, instance, color):
        pass

    @native("func_200502_b", "()Lnet/minecraft/block/material/Material$Builder;")
    def func_200502_b(self, instance):
        return instance

    @native("func_200506_i", "()Lnet/minecraft/block/material/Material;")
    def func_200506_i(self, instance):
        return self.vm.get_class(
            "net/minecraft/block/material/Material", version=self.internal_version
        ).create_instance()


class MaterialColor(NativeClass):
    NAME = "net/minecraft/block/material/MaterialColor"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_151677_p": None,
                "field_151676_q": None,
                "field_151646_E": None,
                "field_193573_Y": None,
                "field_151663_o": None,
                "field_193559_aa": None,
                "field_241540_ac_": None,
                "field_151648_G": None,
                "field_151653_I": None,
                "field_193565_Q": None,
                "field_193562_N": None,
                "field_151645_D": None,
                "field_193561_M": None,
                "field_197655_T": None,
                "field_151666_j": None,
                "field_151671_v": None,
                "field_193567_S": None,
                "field_151664_l": None,
                "field_151678_z": None,
                "field_151654_J": None,
                "field_193566_R": None,
                "field_151665_m": None,
                "field_151670_w": None,
                "field_151679_y": None,
                "field_151649_A": None,
                "field_193564_P": None,
                "field_193572_X": None,
                "field_193571_W": None,
                "field_193568_T": None,
                "field_197656_x": None,
                "field_151675_r": None,
                "field_151655_K": None,
                "field_151660_b": None,
                "field_151668_h": None,
            }
        )


class MaterialPushReaction(NativeClass):
    NAME = "net/minecraft/block/material/PushReaction"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "NORMAL": "net/minecraft/block/material/PushReaction::NORMAL",
                "DESTROY": "net/minecraft/block/material/PushReaction::DESTROY",
                "PUSH_ONLY": "net/minecraft/block/material/PushReaction::DESTROY",
                "BLOCK": "net/minecraft/block/material/PushReaction::BLOCK",
            }
        )


class AbstractGlassBlock(Block):
    NAME = "net/minecraft/block/AbstractGlassBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class FireBlock(Block):
    NAME = "net/minecraft/block/FireBlock"

    @native("func_180686_a", "(Lnet/minecraft/block/Block;II)V")
    def func_180686_a(self, instance, block_class, a, b):
        pass


class ComposterBlock(Block):
    NAME = "net/minecraft/block/ComposterBlock"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({"field_220299_b": {}})


class SandBlock(Block):
    NAME = "net/minecraft/block/SandBlock"

    @native("<init>", "(ILnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, value, properties):
        instance.properties = properties


class DirectionalBlock(Block):
    NAME = "net/minecraft/block/DirectionalBlock"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_176387_N": None,
            }
        )


class StairsBlock(Block):
    NAME = "net/minecraft/block/StairsBlock"

    @native(
        "<init>",
        "(Lnet/minecraft/block/BlockState;Lnet/minecraft/block/AbstractBlock$Properties;)V",
    )
    def init(self, instance, a, properties):
        instance.properties = properties


class SlabBlock(Block):
    NAME = "net/minecraft/block/SlabBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class WallBlock(Block):
    NAME = "net/minecraft/block/WallBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class GrassBlock(Block):
    NAME = "net/minecraft/block/GrassBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class HorizontalFaceBlock(Block):
    NAME = "net/minecraft/block/HorizontalFaceBlock"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_196366_M": None,
                "field_185512_D": None,
            }
        )

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties

    @native("func_180632_j", "(Lnet/minecraft/block/BlockState;)V")
    def func_180632_j(self, instance, state):
        pass

    def get_dynamic_field_keys(self):
        return super().get_dynamic_field_keys() | {"field_176227_L"}


class HugeMushroomBlock(Block):
    NAME = "net/minecraft/block/HugeMushroomBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class SaplingBlock(Block):
    NAME = "net/minecraft/block/SaplingBlock"

    @native(
        "<init>",
        "(Lnet/minecraft/block/trees/Tree;Lnet/minecraft/block/AbstractBlock$Properties;)V",
    )
    def init(self, instance, tree, properties):
        instance.properties = properties

    @native("func_180632_j", "(Lnet/minecraft/block/BlockState;)V")
    def func_180632_j(self, instance, block_state):
        pass

    def get_dynamic_field_keys(self):
        return super().get_dynamic_field_keys() | {"field_176227_L"}


class LeavesBlock(Block):
    NAME = "net/minecraft/block/LeavesBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class RotatedPillarBlock(Block):
    NAME = "net/minecraft/block/RotatedPillarBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class FenceBlock(Block):
    NAME = "net/minecraft/block/FenceBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class FenceGateBlock(Block):
    NAME = "net/minecraft/block/FenceGateBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class DoorBlock(Block):
    NAME = "net/minecraft/block/DoorBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class TrapDoorBlock(Block):
    NAME = "net/minecraft/block/TrapDoorBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class PressurePlateBlock(Block):
    NAME = "net/minecraft/block/PressurePlateBlock"

    @native(
        "<init>",
        "(Lnet/minecraft/block/PressurePlateBlock$Sensitivity;Lnet/minecraft/block/AbstractBlock$Properties;)V",
    )
    def init(self, instance, sensitivity, properties):
        instance.properties = properties


class PressurePlateBlock_Sensitivity(NativeClass):
    NAME = "net/minecraft/block/PressurePlateBlock$Sensitivity"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "EVERYTHING": "net/minecraft/block/PressurePlateBlock$Sensitivity::EVERYTHING"
            }
        )


class WoodButtonBlock(Block):
    NAME = "net/minecraft/block/WoodButtonBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class FlowerBlock(Block):
    NAME = "net/minecraft/block/FlowerBlock"

    @native(
        "<init>",
        "(Lnet/minecraft/potion/Effect;ILnet/minecraft/block/AbstractBlock$Properties;)V",
    )
    def init(self, instance, effect, level, properties):
        instance.properties = properties


class TallFlowerBlock(Block):
    NAME = "net/minecraft/block/TallFlowerBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class DoublePlantBlock(Block):
    NAME = "net/minecraft/block/DoublePlantBlock"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({"field_176492_b": None})

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties

    @native("func_180632_j", "(Lnet/minecraft/block/BlockState;)V")
    def func_180632_j(self, instance, state):
        pass

    def get_dynamic_field_keys(self):
        return super().get_dynamic_field_keys() | {"field_176227_L"}


class VineBlock(Block):
    NAME = "net/minecraft/block/VineBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties


class BushBlock(Block):
    NAME = "net/minecraft/block/BushBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties

    @native("func_208617_a", "(DDDDDD)Lnet/minecraft/util/math/shapes/VoxelShape;")
    def func_208617_a(self, *_):
        pass

class IWaterLoggable(NativeClass):
    NAME = "net/minecraft/block/IWaterLoggable"


class HorizontalBlock(Block):
    NAME = "net/minecraft/block/HorizontalBlock"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_185512_D": None,
            }
        )

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties

    @native("func_180632_j", "(Lnet/minecraft/block/BlockState;)V")
    def func_180632_j(self, instance, state):
        pass

    @native("func_176223_P", "()Lnet/minecraft/block/BlockState;")
    def func_176223_P(self, instance):
        return instance


class SixWayBlock(Block):
    NAME = "net/minecraft/block/SixWayBlock"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_196488_a": None,
                "field_196490_b": None,
                "field_196492_c": None,
                "field_196495_y": None,
                "field_196496_z": None,
                "field_196489_A": None,
            }
        )

    @native("<init>", "(FLnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, value, properties):
        instance.properties = properties

    @native("func_180632_j", "(Lnet/minecraft/block/BlockState;)V")
    def func_180632_j(self, instance, state):
        pass


class MushroomBlock(Block):
    NAME = "net/minecraft/block/MushroomBlock"

    @native("<init>", "(Lnet/minecraft/block/AbstractBlock$Properties;)V")
    def init(self, instance, properties):
        instance.properties = properties

    @native("func_208617_a", "(DDDDDD)Lnet/minecraft/util/math/shapes/VoxelShape;")
    def func_208617_a(self, *_):
        pass


class FlowerPotBlock(Block):
    NAME = "net/minecraft/block/FlowerPotBlock"

    @native(
        "<init>",
        "(Lnet/minecraft/block/Block;Lnet/minecraft/block/AbstractBlock$Properties;)V",
    )
    def init(self, instance, block, properties):
        instance.properties = properties


class AbstractTopPlantBlock(Block):
    NAME = "net/minecraft/block/AbstractTopPlantBlock"

    @native(
        "<init>",
        "(Lnet/minecraft/block/AbstractBlock$Properties;Lnet/minecraft/util/Direction;Lnet/minecraft/util/math/shapes/VoxelShape;ZD)V",
    )
    def init(self, instance, properties, direction, shape, a, b):
        instance.properties = properties


class AbstractBodyPlantBlock(Block):
    NAME = "net/minecraft/block/AbstractBodyPlantBlock"

    @native(
        "<init>",
        "(Lnet/minecraft/block/AbstractBlock$Properties;Lnet/minecraft/util/Direction;Lnet/minecraft/util/math/shapes/VoxelShape;Z)V",
    )
    def init(self, instance, properties, direction, shape, a):
        instance.properties = properties


class StandingSignBlock(Block):
    NAME = "net/minecraft/block/StandingSignBlock"


class IPlantable(NativeClass):
    NAME = "net/minecraftforge/common/IPlantable"


class IGrowable(NativeClass):
    NAME = "net/minecraft/block/IGrowable"


class Item(NativeClass):
    NAME = "net/minecraft/item/Item"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_111210_e": None,
            }
        )

    def create_instance(self):
        instance = super().create_instance()
        instance.properties = None
        instance.registry_name = None
        return instance

    @native("<init>", "(Lnet/minecraft/item/Item$Properties;)V")
    def init(self, instance, properties):
        try:
            instance.properties = properties
        except AttributeError:
            raise StackCollectingException(
                f"It is not working! Something is wrong with {instance}"
            )

    @native(
        "setRegistryName",
        "(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, name):
        instance.registry_name = name
        return instance

    @native(
        "setRegistryName",
        "(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName2(self, instance, name):
        instance.registry_name = name if isinstance(name, str) else name.name
        return instance

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName3(self, instance, namespace, name):
        return instance

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName4(self, instance, namespace, name):
        instance.registry_name = namespace + ":" + name
        return instance

    @native("getRegistryName", "()Lnet/minecraft/util/ResourceLocation;")
    def getRegistryName(self, instance):
        return instance.registry_name

    @native("func_70067_L", "()Z")
    def func_70067_L(self, instance):
        return 0

    @native("func_77658_a", "()Ljava/lang/String;")
    def func_77658_a(self, instance):
        return "MissingImplementation"

    @native("getItem", "()Lnet/minecraft/item/Item;")
    def getItem(self, instance):
        return instance


class Items(NativeClass):
    NAME = "net/minecraft/item/Items"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_151137_ax": None,
                "field_222027_iT": None,
                "field_151133_ar": None,
                "field_151129_at": None,
                "field_151117_aB": None,
                "field_151131_as": None,
                "field_151068_bn": None,
            }
        )


class Item_Properties(NativeClass):
    NAME = "net/minecraft/item/Item$Properties"

    def create_instance(self):
        instance = super().create_instance()
        instance.item_group = None
        instance.rarity = None
        return instance

    @native("<init>", "()V")
    def init(self, instance):
        pass

    @native(
        "func_200916_a",
        "(Lnet/minecraft/item/ItemGroup;)Lnet/minecraft/item/Item$Properties;",
    )
    def setItemGroup(self, instance, item_group):
        instance.item_group = item_group
        return instance

    @native(
        "func_208103_a",
        "(Lnet/minecraft/item/Rarity;)Lnet/minecraft/item/Item$Properties;",
    )
    def setRarity(self, instance, rarity):
        instance.rarity = rarity
        return instance

    @native("func_200917_a", "(I)Lnet/minecraft/item/Item$Properties;")
    def func_200917_a(self, instance, value):
        return instance

    @native("func_200918_c", "(I)Lnet/minecraft/item/Item$Properties;")
    def func_200918_c(self, instance, level):
        return instance

    @native("setNoRepair", "()Lnet/minecraft/item/Item$Properties;")
    def setNoRepair(self, instance):
        return instance

    @native("func_234689_a_", "()Lnet/minecraft/item/Item$Properties;")
    def func_234689_a_(self, instance):
        return instance

    @native(
        "addToolType",
        "(Lnet/minecraftforge/common/ToolType;I)Lnet/minecraft/item/Item$Properties;",
    )
    def addToolType(self, instance, tool_type, v):
        return instance


class Food__Builder(NativeClass):
    NAME = "net/minecraft/item/Food$Builder"

    @native("<init>", "()V")
    def init(self, instance):
        pass

    @native("func_221456_a", "(I)Lnet/minecraft/item/Food$Builder;")
    def func_221456_a(self, instance, v):
        return instance

    @native("func_221454_a", "(F)Lnet/minecraft/item/Food$Builder;")
    def func_221454_a(self, instance, v):
        return instance

    @native(
        "effect", "(Ljava/util/function/Supplier;F)Lnet/minecraft/item/Food$Builder;"
    )
    def effect(self, instance, supplier, v: float):
        return instance

    @native("func_221455_b", "()Lnet/minecraft/item/Food$Builder;")
    def func_221455_b(self, instance):
        return instance

    @native("func_221453_d", "()Lnet/minecraft/item/Food;")
    def func_221453_d(self, instance):
        return self.vm.get_class(
            "net/minecraft/item/Food", version=self.internal_version
        ).create_instance()


class Food(NativeClass):
    NAME = "net/minecraft/item/Food"


class ItemGroup(NativeClass):
    NAME = "net/minecraft/item/ItemGroup"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                # Exposed for a ID of the tab, as mc requires it for no reason. We don't need it
                "field_78032_a": [],
                "field_78040_i": None,
                "field_78026_f": None,
                "field_78037_j": None,
            }
        )

    @native("<init>", "(ILjava/lang/String;)V")
    def init(self, instance, a: int, name: str):
        import mcpython.client.gui.InventoryCreativeTab

        try:
            instance.fields[
                "underlying_tab"
            ] = mcpython.client.gui.InventoryCreativeTab.CreativeItemTab(
                name,
                mcpython.common.container.ResourceStack.ItemStack("minecraft:barrier"),
            )
        except:
            raise StackCollectingException(
                f"something went wrong here in ItemGroup init working on {instance}"
            )

        @shared.mod_loader("minecraft", "stage:item_groups:load")
        def add_tab():
            import jvm.Runtime

            runtime = jvm.Runtime.Runtime()

            # create the item stack
            try:
                stack = runtime.run_method(
                    instance.get_class().get_method(
                        "func_78016_d", "()Lnet/minecraft/item/ItemStack;"
                    )
                )
            except StackCollectingException as e:
                e.add_trace(f"during creating ItemStack for item group {name}")
                raise

            instance.fields["underlying_tab"].icon = stack.underlying_stack
            mcpython.client.gui.InventoryCreativeTab.CT_MANAGER.add_tab(
                instance.fields["underlying_tab"]
            )

    @native("<init>", "(Ljava/lang/String;)V")
    def init2(self, instance, name: str):
        self.init(instance, -1, name)

    @native("func_78014_h", "()Lnet/minecraft/item/ItemGroup;")
    def func_78014_h(self, instance):
        return instance

    @native("func_78025_a", "(Ljava/lang/String;)Lnet/minecraft/item/ItemGroup;")
    def func_78025_a(self, instance, v: str):
        return instance

    @native("getGroupCountSafe", "()I")
    def getGroupCountSafe(self, *_):
        return -1

    def get_dynamic_field_keys(self):
        return {"underlying_tab"}


class ItemStack(NativeClass):
    NAME = "net/minecraft/item/ItemStack"

    @native("<init>", "(Lnet/minecraft/util/IItemProvider;)V")
    def init(self, instance, item_provider):
        import mcpython.common.container.ResourceStack

        instance.underlying_stack = mcpython.common.container.ResourceStack.ItemStack()

    @native("<init>", "(Lnet/minecraft/util/IItemProvider;I)V")
    def init2(self, instance, item_provider, size):
        import mcpython.common.container.ResourceStack

        instance.underlying_stack = mcpython.common.container.ResourceStack.ItemStack()

    @native("func_190926_b", "()Z")
    def func_190926_b(self, instance):
        return 0


class IItemTier(NativeClass):
    NAME = "net/minecraft/item/IItemTier"

    @native("func_200926_a", "()I")
    def func_200926_a(self, instance):
        return 0


class ItemTier(IItemTier):
    NAME = "net/minecraft/item/ItemTier"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "STONE": 2,
                "IRON": 3,
                "DIAMOND": 4,
            }
        )

    @native("func_200926_a", "()I")
    def func_200926_a(self, instance):
        return instance


class BlockItem(Item):
    NAME = "net/minecraft/item/BlockItem"

    @native(
        "<init>", "(Lnet/minecraft/block/Block;Lnet/minecraft/item/Item$Properties;)V"
    )
    def init(self, instance, block, properties):
        if instance is None:
            return

        instance.block = block
        instance.properties = properties

    @native(
        "setRegistryName",
        "(Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, name: str):
        instance.registry_name = name
        return instance

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName2(self, instance, namespace: str, name: str):
        instance.registry_name = namespace + ":" + name
        return instance

    @native(
        "setRegistryName",
        "(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName3(self, instance, name):
        instance.registry_name = name if isinstance(name, str) else name.name
        return instance


class AxeItem(Item):
    NAME = "net/minecraft/item/AxeItem"

    def __init__(self):
        super().__init__()
        self.exposed_attributes = {"field_203176_a": {}}

    @native(
        "<init>",
        "(Lnet/minecraft/item/IItemTier;FFLnet/minecraft/item/Item$Properties;)V",
    )
    def init(self, instance, tier, a, b, properties):
        instance.properties = properties

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, namespace, name):
        instance.name = namespace + ":" + name
        return instance


class BucketItem(Item):
    NAME = "net/minecraft/item/BucketItem"

    @native(
        "<init>", "(Ljava/util/function/Supplier;Lnet/minecraft/item/Item$Properties;)V"
    )
    def init(self, *_):
        pass


class HoeItem(Item):
    NAME = "net/minecraft/item/HoeItem"

    def __init__(self):
        super().__init__()
        self.exposed_attributes = {
            "field_195973_b": {},
        }

    @native(
        "<init>",
        "(Lnet/minecraft/item/IItemTier;IFLnet/minecraft/item/Item$Properties;)V",
    )
    def init(self, instance, tier, a, b, properties):
        instance.properties = properties

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, namespace, name):
        instance.name = namespace + ":" + name
        return instance


class PickaxeItem(Item):
    NAME = "net/minecraft/item/PickaxeItem"

    @native(
        "<init>",
        "(Lnet/minecraft/item/IItemTier;IFLnet/minecraft/item/Item$Properties;)V",
    )
    def init(self, instance, tier, a, b, properties):
        instance.properties = properties

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, namespace, name):
        instance.name = namespace + ":" + name
        return instance


class ShovelItem(Item):
    NAME = "net/minecraft/item/ShovelItem"

    def __init__(self):
        super().__init__()
        self.exposed_attributes = {"field_195955_e": {}}

    @native(
        "<init>",
        "(Lnet/minecraft/item/IItemTier;FFLnet/minecraft/item/Item$Properties;)V",
    )
    def init(self, instance, tier, a, b, properties):
        instance.properties = properties

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, namespace, name):
        instance.name = namespace + ":" + name
        return instance


class SwordItem(Item):
    NAME = "net/minecraft/item/SwordItem"

    @native(
        "<init>",
        "(Lnet/minecraft/item/IItemTier;IFLnet/minecraft/item/Item$Properties;)V",
    )
    def init(self, instance, tier, a, b, properties):
        instance.properties = properties

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, namespace, name):
        instance.name = namespace + ":" + name
        return instance


class MusicDiscItem(Item):
    NAME = "net/minecraft/item/MusicDiscItem"

    @native(
        "<init>",
        "(ILjava/util/function/Supplier;Lnet/minecraft/item/Item$Properties;)V",
    )
    def init(self, instance, value, supplier, properties):
        instance.properties = properties


class IItemProvider(NativeClass):
    NAME = "net/minecraft/util/IItemProvider"

    @native("func_199767_j", "()Lnet/minecraft/item/Item;")
    def getItem(self, instance):
        pass


class ItemRarity(NativeClass):
    NAME = "net/minecraft/item/Rarity"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "RARE": "net/minecraft/item/Rarity::RARE",
                "UNCOMMON": "net/minecraft/item/Rarity::UNCOMMON",
                "EPIC": "net/minecraft/item/Rarity::EPIC",
            }
        )


class DyeColor(NativeClass):
    NAME = "net/minecraft/item/DyeColor"

    def __init__(self):
        super().__init__()
        import mcpython.util.enums

        self.colors = mcpython.util.enums.COLORS

        self.exposed_attributes.update({color.upper(): color for color in self.colors})

    @native("values", "()[Lnet/minecraft/item/DyeColor;")
    def values(self):
        return self.colors

    @native("func_176610_l", "()Ljava/lang/String;")
    def func_176610_l(self, instance):
        return instance

    @native("ordinal", "()I")
    def ordinal(self, instance):
        return self.colors.index(instance)


class AttachFace(NativeClass):
    NAME = "net/minecraft/state/properties/AttachFace"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "FLOOR": "net/minecraft/state/properties/AttachFace::FLOOR",
                "WALL": "net/minecraft/state/properties/AttachFace::WALL",
                "CEILING": "net/minecraft/state/properties/AttachFace::CEILING",
            }
        )

    @native("values", "()[Lnet/minecraft/state/properties/AttachFace;")
    def values(self):
        return list(self.exposed_attributes.keys())

    @native("ordinal", "()I")
    def ordinal(self, instance):
        return 0


class BlockState(NativeClass):
    NAME = "net/minecraft/block/BlockState"

    @native(
        "func_206870_a",
        "(Lnet/minecraft/state/Property;Ljava/lang/Comparable;)Ljava/lang/Object;",
    )
    def func_206870_a(self, instance, prop, value):
        pass


class BlockStateProperties(NativeClass):
    NAME = "net/minecraft/state/properties/BlockStateProperties"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_208137_al": None,
                "field_208198_y": None,
                "field_208155_H": None,
                "field_208157_J": None,
                "field_208194_u": None,
            }
        )


class BooleanProperty(NativeClass):
    NAME = "net/minecraft/state/BooleanProperty"

    @native(
        "func_177716_a", "(Ljava/lang/String;)Lnet/minecraft/state/BooleanProperty;"
    )
    def func_177716_a(self, string):
        return self.create_instance()


class IntegerProperty(NativeClass):
    NAME = "net/minecraft/state/IntegerProperty"

    @native(
        "func_177719_a", "(Ljava/lang/String;II)Lnet/minecraft/state/IntegerProperty;"
    )
    def func_177719_a(self, *_):
        pass


class DoubleBlockHalf(NativeClass):
    NAME = "net/minecraft/state/properties/DoubleBlockHalf"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {"LOWER": "net/minecraft/state/properties/DoubleBlockHalf::UPPER"}
        )


class Direction(NativeClass):
    NAME = "net/minecraft/util/Direction"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "NORTH": ("net/minecraft/util/Direction::NORTH", (0, 1, 0)),
                "SOUTH": ("net/minecraft/util/Direction::SOUTH", (0, -1, 0)),
                "WEST": ("net/minecraft/util/Direction::WEST", (-1, 0, 0)),
                "EAST": ("net/minecraft/util/Direction::EAST", (1, 0, 0)),
                "DOWN": ("net/minecraft/util/Direction::DOWN", (0, 0, -1)),
                "UP": ("net/minecraft/util/Direction::UP", (0, 0, 1)),
            }
        )

    @native("values", "()[Lnet/minecraft/util/Direction;")
    def values(self):
        return list(self.exposed_attributes.values())

    @native("ordinal", "()I")
    def ordinal(self, instance):
        return 0

    @native("func_82601_c", "()I")
    def getXOffset(self, instance):
        return instance[1][0]

    @native("func_96559_d", "()I")
    def getYOffset(self, instance):
        return instance[1][1]

    @native("func_82599_e", "()I")
    def getZOffset(self, instance):
        return instance[1][2]


class Direction__Axis(NativeClass):
    NAME = "net/minecraft/util/Direction$Axis"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "X": 0,
            "Y": 1,
            "Z": 2,
        })


class EnumProperty(NativeClass):
    NAME = "net/minecraft/state/EnumProperty"

    @native(
        "func_177709_a",
        "(Ljava/lang/String;Ljava/lang/Class;)Lnet/minecraft/state/EnumProperty;",
    )
    def func_1777709_a(self, name, cls):
        return self.create_instance()

    @native("func_177708_a",
            "(Ljava/lang/String;Ljava/lang/Class;Ljava/util/function/Predicate;)Lnet/minecraft/state/EnumProperty;")
    def func_177708_a(self, name, cls, predicate):
        return self.create_instance()


class Tree(NativeClass):
    NAME = "net/minecraft/block/trees/Tree"

    @native("<init>", "()V")
    def init(self, instance):
        pass


class BigTree(NativeClass):
    NAME = "net/minecraft/block/trees/BigTree"

    @native("<init>", "()V")
    def init(self, instance):
        pass


class EntityPredicates(NativeClass):
    NAME = "net/minecraft/util/EntityPredicates"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_180132_d": None,
            }
        )


class EntityAttributes(NativeClass):
    NAME = "net/minecraft/entity/ai/attributes/Attributes"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_233823_f_": None,
            }
        )


class EntityAttributeModifier(NativeClass):
    NAME = "net/minecraft/entity/ai/attributes/AttributeModifier"

    @native(
        "<init>",
        "(Ljava/util/UUID;Ljava/lang/String;DLnet/minecraft/entity/ai/attributes/AttributeModifier$Operation;)V",
    )
    def init(self, instance, uuid, a: str, b: float, operation):
        pass


class EntityAttributeModifier__Operation(NativeClass):
    NAME = "net/minecraft/entity/ai/attributes/AttributeModifier$Operation"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "ADDITION": "net/minecraft/entity/ai/attributes/AttributeModifier$Operation::ADDITION"
            }
        )


class EntityClassification(NativeClass):
    NAME = "net/minecraft/entity/EntityClassification"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "MISC": None,
            }
        )


class EntityType(NativeClass):
    NAME = "net/minecraft/entity/EntityType"

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, name):
        return instance


class EntityType__Builder(NativeClass):
    NAME = "net/minecraft/entity/EntityType$Builder"

    @native(
        "func_220322_a",
        "(Lnet/minecraft/entity/EntityType$IFactory;Lnet/minecraft/entity/EntityClassification;)Lnet/minecraft/entity/EntityType$Builder;",
    )
    def create(self, factory, classification):
        return self.create_instance()

    @native("func_220321_a", "(FF)Lnet/minecraft/entity/EntityType$Builder;")
    def func_220321_a(self, instance, a, b):
        return instance

    @native(
        "setCustomClientFactory",
        "(Ljava/util/function/BiFunction;)Lnet/minecraft/entity/EntityType$Builder;",
    )
    def setCustomClientFactory(self, instance, function):
        return instance

    @native("func_233606_a_", "(I)Lnet/minecraft/entity/EntityType$Builder;")
    def func_233606_a_(self, instance, v):
        return instance

    @native("func_206830_a", "(Ljava/lang/String;)Lnet/minecraft/entity/EntityType;")
    def func_206830_a(self, instance, v):
        return instance

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, namespace, name):
        return instance

    @native("setTrackingRange", "(I)Lnet/minecraft/entity/EntityType$Builder;")
    def setTrackingRange(self, instance, r: int):
        return instance

    @native("setUpdateInterval", "(I)Lnet/minecraft/entity/EntityType$Builder;")
    def setUpdateInterval(self, instance, interval: int):
        return instance

    @native(
        "setShouldReceiveVelocityUpdates",
        "(Z)Lnet/minecraft/entity/EntityType$Builder;",
    )
    def setShouldReceiveVelocityUpdates(self, instance, should):
        return instance


class Entity(NativeClass):
    NAME = "net/minecraft/entity/Entity"

    @native("func_70067_L", "()Z")
    def func_70067_L(self):
        return 0


class ItemEntity(Entity):
    NAME = "net/minecraft/entity/item/ItemEntity"


class Attribute(NativeClass):
    NAME = "net/minecraft/entity/ai/attributes/Attribute"


class TranslationTextComponent(NativeClass):
    NAME = "net/minecraft/util/text/TranslationTextComponent"

    @native("<init>", "(Ljava/lang/String;)V")
    def init(self, instance, lookup_string):
        pass


class TileEntityType(NativeClass):
    NAME = "net/minecraft/tileentity/TileEntityType"


class TileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/TileEntity"


class BeaconTileEntity(TileEntity):
    NAME = "net/minecraft/tileentity/BeaconTileEntity"


class BannerTileEntity(TileEntity):
    NAME = "net/minecraft/tileentity/BannerTileEntity"


class BrewingStandTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/BrewingStandTileEntity"


class ChestTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/ChestTileEntity"


class CommandBlockTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/CommandBlockTileEntity"


class ComparatorTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/ComparatorTileEntity"


class DaylightDetectorTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/DaylightDetectorTileEntity"


class DispenserTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/DispenserTileEntity"


class DropperTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/DropperTileEntity"


class EnchantingTableTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/EnchantingTableTileEntity"


class EnderChestTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/EnderChestTileEntity"


class EndPortalTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/EndPortalTileEntity"


class FurnaceTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/FurnaceTileEntity"


class HopperTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/HopperTileEntity"


class MobSpawnerTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/MobSpawnerTileEntity"


class PistonTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/PistonTileEntity"


class ShulkerBoxTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/ShulkerBoxTileEntity"


class SignTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/SignTileEntity"


class SkullTileEntity(NativeClass):
    NAME = "net/minecraft/tileentity/SkullTileEntity"


class PaintingType(NativeClass):
    NAME = "net/minecraft/entity/item/PaintingType"


class Fluid(NativeClass):
    NAME = "net/minecraft/fluid/Fluid"


class ForgeFlowingFluid__Properties(NativeClass):
    NAME = "net/minecraftforge/fluids/ForgeFlowingFluid$Properties"

    @native(
        "<init>",
        "(Ljava/util/function/Supplier;Ljava/util/function/Supplier;Lnet/minecraftforge/fluids/FluidAttributes$Builder;)V",
    )
    def init(self, *_):
        pass

    @native(
        "bucket",
        "(Ljava/util/function/Supplier;)Lnet/minecraftforge/fluids/ForgeFlowingFluid$Properties;",
    )
    def bucket(self, *_):
        pass

    @native(
        "block",
        "(Ljava/util/function/Supplier;)Lnet/minecraftforge/fluids/ForgeFlowingFluid$Properties;",
    )
    def block(self, *_):
        pass


class FluidAttributes(NativeClass):
    NAME = "net/minecraftforge/fluids/FluidAttributes"

    @native(
        "builder",
        "(Lnet/minecraft/util/ResourceLocation;Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/fluids/FluidAttributes$Builder;",
    )
    def builder(self, *_):
        pass


class FlowingFluid(NativeClass):
    NAME = "net/minecraft/fluid/FlowingFluid"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_207210_b": None,
            }
        )

    @native("<init>", "()V")
    def init(self, *_):
        pass

    @native(
        "setRegistryName",
        "(Ljava/lang/String;Ljava/lang/String;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, namespace, name):
        return instance

    @native(
        "setRegistryName",
        "(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName2(self, instance, name):
        return instance

    @native("func_207182_e", "()Lnet/minecraft/state/StateContainer;")
    def func_207182_e(self, *_):
        pass


class FlowingFluidBlock(Block):
    NAME = "net/minecraft/block/FlowingFluidBlock"

    @native(
        "<init>",
        "(Ljava/util/function/Supplier;Lnet/minecraft/block/AbstractBlock$Properties;)V",
    )
    def init(self, *_):
        pass

    @native(
        "setRegistryName",
        "(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, name):
        instance.registry_name = name
        return instance


class FluidState(NativeClass):
    NAME = "net/minecraft/fluid/FluidState"

    @native(
        "func_206870_a",
        "(Lnet/minecraft/state/Property;Ljava/lang/Comparable;)Ljava/lang/Object;",
    )
    def func_206870_a(self, *_):
        pass

    @native("func_207183_f", "(Lnet/minecraft/fluid/FluidState;)V")
    def func_207183_f(self, *_):
        pass
