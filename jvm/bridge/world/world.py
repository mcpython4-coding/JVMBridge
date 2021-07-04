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


class World(NativeClass):
    NAME = "net/minecraft/world/World"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_234918_g_": None,
                "field_234919_h_": None,
                "field_234920_i_": None,
                "field_239699_ae_": None,
            }
        )


class Structure(NativeClass):
    NAME = "net/minecraft/world/gen/feature/structure/Structure"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_236365_a_": None,
            }
        )

    @native(
        "func_236391_a_",
        "(Lnet/minecraft/world/gen/feature/IFeatureConfig;)Lnet/minecraft/world/gen/feature/StructureFeature;",
    )
    def func_236391_a_(self, instance, config):
        pass

    @native("<init>", "(Lcom/mojang/serialization/Codec;)V")
    def init(self, *_):
        pass

    @native(
        "setRegistryName",
        "(Lnet/minecraft/util/ResourceLocation;)Lnet/minecraftforge/registries/IForgeRegistryEntry;",
    )
    def setRegistryName(self, instance, name):
        instance.registry_name = name if isinstance(name, str) else name.name

    @native("getRegistryName", "()Lnet/minecraft/util/ResourceLocation;")
    def getRegistryName(self, instance):
        return instance.registry_name


class StructureFeatures(NativeClass):
    NAME = "net/minecraft/world/gen/feature/structure/StructureFeatures"

    @native("func_244162_a",
            "(Ljava/lang/String;Lnet/minecraft/world/gen/feature/StructureFeature;)Lnet/minecraft/world/gen/feature/StructureFeature;")
    def func_244162_a(self, *_):
        pass


class Features(NativeClass):
    NAME = "net/minecraft/world/gen/feature/Features"

    @native("func_243968_a",
            "(Ljava/lang/String;Lnet/minecraft/world/gen/feature/ConfiguredFeature;)Lnet/minecraft/world/gen/feature/ConfiguredFeature;")
    def func_243968_a(self, *_):
        pass


class DimensionStructuresSettings(NativeClass):
    NAME = "net/minecraft/world/gen/settings/DimensionStructuresSettings"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_236191_b_": None,
            }
        )


class StructureSeparationSettings(NativeClass):
    NAME = "net/minecraft/world/gen/settings/StructureSeparationSettings"

    @native("<init>", "(III)V")
    def init(self, instance, x, y, z):
        pass


class FlatGenerationSettings(NativeClass):
    NAME = "net/minecraft/world/gen/FlatGenerationSettings"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_202247_j": None,
            }
        )


class BiomeGeneratorTypeScreens(NativeClass):
    NAME = "net/minecraft/client/gui/screen/BiomeGeneratorTypeScreens"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_239068_c_": None,
            }
        )

    @native("<init>", "(Ljava/lang/String;)V")
    def init(self, instance, v: str):
        pass


class Feature(NativeClass):
    NAME = "net/minecraft/world/gen/feature/Feature"

    @native("<init>", "(Lcom/mojang/serialization/Codec;)V")
    def init(self, instance, codec):
        pass

    @native(
        "func_225566_b_",
        "(Lnet/minecraft/world/gen/feature/IFeatureConfig;)Lnet/minecraft/world/gen/feature/ConfiguredFeature;",
    )
    def func_225566_b_(self, instance, config):
        return instance

    @native(
        "func_227228_a_",
        "(Lnet/minecraft/world/gen/placement/ConfiguredPlacement;)Lnet/minecraft/world/gen/feature/ConfiguredFeature;",
    )
    def func_227228_a_(self, instance, config):
        return instance


class ConfiguredFeature(NativeClass):
    NAME = "net/minecraft/world/gen/feature/ConfiguredFeature"

    @native(
        "func_227228_a_",
        "(Lnet/minecraft/world/gen/placement/ConfiguredPlacement;)Lnet/minecraft/world/gen/feature/ConfiguredFeature;",
    )
    def func_227228_a_(self, *_):
        pass


class NoFeatureConfig(NativeClass):
    NAME = "net/minecraft/world/gen/feature/NoFeatureConfig"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_236558_a_": None,
                "field_236559_b_": None,
            }
        )


class Placement(NativeClass):
    NAME = "net/minecraft/world/gen/placement/Placement"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_215022_h": 0,
            }
        )

    @native(
        "func_227446_a_",
        "(Lnet/minecraft/world/gen/placement/IPlacementConfig;)Lnet/minecraft/world/gen/placement/ConfiguredPlacement;",
    )
    def func_227446_a_(self, instance, config):
        pass


class IPlacementConfig(NativeClass):
    NAME = "net/minecraft/world/gen/placement/IPlacementConfig"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({"field_202468_e": None})


class Biome(NativeClass):
    NAME = "net/minecraft/world/biome/Biome"


class Biome__Category(NativeClass):
    NAME = "net/minecraft/world/biome/Biome$Category"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "NETHER": 0,
                "THEEND": 1,
                "ICY": 2,
                "MUSHROOM": 3,
                "BEACH": 4,
                "DESERT": 5,
                "EXTREME_HILLS": 6,
                "FOREST": 7,
                "JUNGLE": 8,
                "MESA": 9,
                "PLAINS": 12,
                "RIVER": 11,
                "SAVANNA": 12,
                "SWAMP": 13,
                "TAIGA": 14,
            }
        )


class PlainsVillagePools(NativeClass):
    NAME = "net/minecraft/world/gen/feature/structure/PlainsVillagePools"

    @native("func_214744_a", "()V")
    def func_214744_a(self, *_):
        pass


class SavannaVillagePools(NativeClass):
    NAME = "net/minecraft/world/gen/feature/structure/SavannaVillagePools"

    @native("func_214745_a", "()V")
    def func_214745_a(self, *_):
        pass


class TaigaVillagePools(NativeClass):
    NAME = "net/minecraft/world/gen/feature/structure/TaigaVillagePools"

    @native("func_214806_a", "()V")
    def func_214806_a(self, *_):
        pass


class DesertVillagePools(NativeClass):
    NAME = "net/minecraft/world/gen/feature/structure/DesertVillagePools"

    @native("func_222739_a", "()V")
    def func_222739_a(self, *_):
        pass


class SnowyVillagePools(NativeClass):
    NAME = "net/minecraft/world/gen/feature/structure/SnowyVillagePools"

    @native("func_214746_a", "()V")
    def func_214746_a(self, *_):
        pass


class ForgeChunkManager(NativeClass):
    NAME = "net/minecraftforge/common/world/ForgeChunkManager"

    @native(
        "setForcedChunkLoadingCallback",
        "(Ljava/lang/String;Lnet/minecraftforge/common/world/ForgeChunkManager$LoadingValidationCallback;)V",
    )
    def setForcedChunkLoadingCallback(self, *_):
        pass


class Stats(NativeClass):
    NAME = "net/minecraft/stats/Stats"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({"field_199092_j": None})

    @native("func_199084_a",
            "(Ljava/lang/String;Lnet/minecraft/stats/IStatFormatter;)Lnet/minecraft/util/ResourceLocation;")
    def func_199084_a(self, *_):
        pass


class IStatFormatter(NativeClass):
    NAME = "net/minecraft/stats/IStatFormatter"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "field_223218_b_": None,
            }
        )


class StatType(NativeClass):
    NAME = "net/minecraft/stats/StatType"

    @native(
        "func_199077_a",
        "(Ljava/lang/Object;Lnet/minecraft/stats/IStatFormatter;)Lnet/minecraft/stats/Stat;",
    )
    def func_199077_a(self, instance, obj, formatter):
        pass


class AbstractSpawner(NativeClass):
    NAME = "net/minecraft/world/spawner/AbstractSpawner"

    @native("func_98279_f", "()Z")
    def func_98279_f(self, *_):
        pass

    @native("func_98273_j", "()V")
    def func_98273_j(self, *_):
        pass


class WorldEntitySpawner(NativeClass):
    NAME = "net/minecraft/world/spawner/WorldEntitySpawner"


class ClientWorld__ClientWorldInfo(NativeClass):
    NAME = "net/minecraft/client/world/ClientWorld$ClientWorldInfo"


class Dimension(NativeClass):
    NAME = "net/minecraft/world/Dimension"


class DimensionType(NativeClass):
    NAME = "net/minecraft/world/DimensionType"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "field_236001_e_": None,
        })

    @native("<init>",
            "(Ljava/util/OptionalLong;ZZZZDZZZZILnet/minecraft/util/ResourceLocation;Lnet/minecraft/util/ResourceLocation;F)Lnet/minecraft/world/DimensionType;")
    def init(self, *_):
        pass


class WorldLightManager(NativeClass):
    NAME = "net/minecraft/world/lighting/WorldLightManager"


class BiomeGenerationSettings__Builder(NativeClass):
    NAME = "net/minecraft/world/biome/BiomeGenerationSettings$Builder"


class GameRules(NativeClass):
    NAME = "net/minecraft/world/GameRules"


class GameRules__Category(NativeClass):
    NAME = "net/minecraft/world/GameRules$Category"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "UPDATES": 0,
        })


class GameRules__BooleanValue(NativeClass):
    NAME = "net/minecraft/world/GameRules$BooleanValue"

    @native("func_223567_b", "(ZLjava/util/function/BiConsumer;)Lnet/minecraft/world/GameRules$RuleType;")
    def func_223567_b(self, *_):
        return self.create_instance()

    @native("func_223568_b", "(Z)Lnet/minecraft/world/GameRules$RuleType;", static=True)
    def func_223568_b(self, v):
        return self.create_instance()


class GameRules__IntegerValue(NativeClass):
    NAME = "net/minecraft/world/GameRules$IntegerValue"

    @native("func_223564_a", "(ILjava/util/function/BiConsumer;)Lnet/minecraft/world/GameRules$RuleType;")
    def func_223564_a(self, *_):
        return self.create_instance()

    @native("func_223559_b", "(I)Lnet/minecraft/world/GameRules$RuleType;")
    def func_223559_b(self, instance, v):
        return instance


class ChunkSerializer(NativeClass):
    NAME = "net/minecraft/world/chunk/storage/ChunkSerializer"


class MobSpawnInfo__Builder(NativeClass):
    NAME = "net/minecraft/world/biome/MobSpawnInfo$Builder"


class ClientWorld(NativeClass):
    NAME = "net/minecraft/client/world/ClientWorld"


class BiomeContainer(NativeClass):
    NAME = "net/minecraft/world/biome/BiomeContainer"


class ChunkStatus(NativeClass):
    NAME = "net/minecraft/world/chunk/ChunkStatus"


class BasaltColumnFeature(NativeClass):
    NAME = "net/minecraft/world/gen/feature/BasaltColumnFeature"


class HillsLayer(NativeClass):
    NAME = "net/minecraft/world/gen/layer/HillsLayer"


class MixRiverLayer(NativeClass):
    NAME = "net/minecraft/world/gen/layer/MixRiverLayer"


class ShoreLayer(NativeClass):
    NAME = "net/minecraft/world/gen/layer/ShoreLayer"


class MixOceansLayer(NativeClass):
    NAME = "net/minecraft/world/gen/layer/MixOceansLayer"


class Difficulty(NativeClass):
    NAME = "net/minecraft/world/Difficulty"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "NORMAL": 1,
        })


class GameSettings(NativeClass):
    NAME = "net/minecraft/client/GameSettings"


class TicketType(NativeClass):
    NAME = "net/minecraft/world/server/TicketType"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "field_219494_g": self.create_instance(),
        })

    @native("func_223183_a", "(Ljava/lang/String;Ljava/util/Comparator;I)Lnet/minecraft/world/server/TicketType;")
    def func_223183_a(self, *_):
        return self.create_instance()


class KeyBinding(NativeClass):
    NAME = "net/minecraft/client/settings/KeyBinding"

    @native("<init>",
            "(Ljava/lang/String;Lnet/minecraftforge/client/settings/IKeyConflictContext;Lnet/minecraft/client/util/InputMappings$Type;ILjava/lang/String;)V")
    def init(self, *_):
        pass

    @native("<init>", "(Ljava/lang/String;ILjava/lang/String;)V")
    def init2(self, *_):
        pass


class InputMappings__Type(NativeClass):
    NAME = "net/minecraft/client/util/InputMappings$Type"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "KEYSYM": 0,
        })


class KeyConflictContext(NativeClass):
    NAME = "net/minecraftforge/client/settings/KeyConflictContext"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "GUI": 0,
        })


class NoiseChunkGenerator(NativeClass):
    NAME = "net/minecraft/world/gen/NoiseChunkGenerator"


class Layer(NativeClass):
    NAME = "net/minecraft/world/gen/layer/Layer"


class ChunkManager(NativeClass):
    NAME = "net/minecraft/world/server/ChunkManager"


class Chunk(NativeClass):
    NAME = "net/minecraft/world/chunk/Chunk"


class ServerWorldInfo(NativeClass):
    NAME = "net/minecraft/world/storage/ServerWorldInfo"


class TemplateManager(NativeClass):
    NAME = "net/minecraft/world/gen/feature/template/TemplateManager"


class DataFixesManager(NativeClass):
    NAME = "net/minecraft/util/datafix/DataFixesManager"


class Template(NativeClass):
    NAME = "net/minecraft/world/gen/feature/template/Template"


class ServerWorld(NativeClass):
    NAME = "net/minecraft/world/server/ServerWorld"


class OreFeature(NativeClass):
    NAME = "net/minecraft/world/gen/feature/OreFeature"

    @native("<init>", "(Lcom/mojang/serialization/Codec;)V")
    def init(self, *_):
        pass


class OreFeatureConfig(NativeClass):
    NAME = "net/minecraft/world/gen/feature/OreFeatureConfig"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "field_236566_a_": None,
        })


class DimensionGeneratorSettings(NativeClass):
    NAME = "net/minecraft/world/gen/settings/DimensionGeneratorSettings"


class ChunkGenerator(NativeClass):
    NAME = "net/minecraft/world/gen/ChunkGenerator"

    @native("func_230347_a_", "()Lcom/mojang/serialization/Codec;")
    def func_230347_a_(self, *_):
        pass


class DungeonsFeature(NativeClass):
    NAME = "net/minecraft/world/gen/feature/DungeonsFeature"


class JigsawPattern(NativeClass):
    NAME = "net/minecraft/world/gen/feature/jigsaw/JigsawPattern"


class TreeFeature(NativeClass):
    NAME = "net/minecraft/world/gen/feature/TreeFeature"


class LakesFeature(NativeClass):
    NAME = "net/minecraft/world/gen/feature/LakesFeature"


class SpringFeature(NativeClass):
    NAME = "net/minecraft/world/gen/feature/SpringFeature"


class PillagerOutpostStructure(NativeClass):
    NAME = "net/minecraft/world/gen/feature/structure/PillagerOutpostStructure"


class SingleJigsawPiece(NativeClass):
    NAME = "net/minecraft/world/gen/feature/jigsaw/SingleJigsawPiece"


class StructurePiece(NativeClass):
    NAME = "net/minecraft/world/gen/feature/structure/StructurePiece"


class StrongholdPieces__Stronghold(NativeClass):
    NAME = "net/minecraft/world/gen/feature/structure/StrongholdPieces$Stronghold"
