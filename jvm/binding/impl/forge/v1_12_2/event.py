import traceback

from jvm.builtinwrapper import handler as builtin_handler
from jvm.JavaExceptionStack import StackCollectingException
from mcpython import shared
from mcpython.common.mod.util import LoadingInterruptException
from mcpython.engine.event.EventHandler import PUBLIC_EVENT_BUS
import jvm.api


class Profiler:
    def __init__(self):
        self.field_76327_a = False


class WorldWrapper:
    def __init__(self):
        # isRemote
        self.field_72995_K = False

        # profiler
        self.field_72984_F = Profiler()

        # worldProvider
        self.field_73011_w = self


class TickEvent:
    world = WorldWrapper()

    def __init__(self):
        self.phase = None
        self.player = shared.world.get_active_player()


EventType2EventStage = {
    "(Lnet/minecraftforge/event/RegistryEvent$NewRegistry;)V": ("stage:registry_addition", lambda e: [None], 0),

    "(Lnet/minecraftforge/event/RegistryEvent$Register;)V": ("stage:post", lambda e: [None], 0),
    "(Lcrazypants/enderio/base/init/RegisterModObject;)V": ("stage:post", lambda e: [None], 0),
    "(Lnet/minecraftforge/client/event/ModelRegistryEvent;)V": ("stage:model:model_create", lambda e: [None], 0),
    "(Lnet/minecraftforge/client/event/TextureStitchEvent$Pre;)V": ("stage:textureatlas:prepare", lambda e: [None], 0),
    "(Lnet/minecraftforge/event/LootTableLoadEvent;)V": ("stage:loottables:load", lambda e: [None], 0),
    "(Lnet/minecraftforge/client/event/ModelBakeEvent;)V": ("stage:model:model_bake", lambda e: [None], 0),
    "(Lcrazypants/enderio/base/events/ModSoundRegisterEvent;)V": None,
    "(Lnet/minecraftforge/event/AttachCapabilitiesEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/AdvancementEvent;)V": None,

    "(Lcom/enderio/core/common/event/ConfigFileChangedEvent;)V": None,
    "(Lnet/minecraftforge/fml/client/event/ConfigChangedEvent$OnConfigChangedEvent;)V": None,

    "(Lnet/minecraftforge/fml/common/gameevent/TickEvent$ClientTickEvent;)V": ("tickhandler:general", lambda e: [TickEvent()], 1),
    "(Lnet/minecraftforge/fml/common/gameevent/TickEvent$ServerTickEvent;)V": ("tickhandler:general", lambda e: [TickEvent()], 1),
    "(Lnet/minecraftforge/fml/common/gameevent/TickEvent$WorldTickEvent;)V": ("tickhandler:general", lambda e: [TickEvent()], 1),
    "(Lnet/minecraftforge/fml/common/gameevent/TickEvent$PlayerTickEvent;)V": ("tickhandler:general", lambda e: [TickEvent()], 1),

    "(Lnet/minecraftforge/event/entity/player/ItemTooltipEvent;)V": None,
    "(Lnet/minecraftforge/client/event/EntityViewRenderEvent$FOVModifier;)V": None,
    "(Lnet/minecraftforge/client/event/RenderBlockOverlayEvent;)V": None,
    "(Lnet/minecraftforge/client/event/EntityViewRenderEvent$FogDensity;)V": None,
    "(Lnet/minecraftforge/client/event/EntityViewRenderEvent$FogColors;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$InitGuiEvent$Post;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$InitGuiEvent$Pre;)V": None,
    "(Lnet/minecraftforge/client/event/DrawBlockHighlightEvent;)V": None,
    "(Lnet/minecraftforge/client/event/RenderPlayerEvent$Pre;)V": None,
    "(Lnet/minecraftforge/client/event/RenderGameOverlayEvent$Post;)V": None,
    "(Lnet/minecraftforge/client/event/RenderWorldLastEvent;)V": None,
    "(Lnet/minecraftforge/client/event/RenderLivingEvent$Post;)V": None,
    "(Lnet/minecraftforge/client/event/RenderLivingEvent$Pre;)V": None,

    "(Lnet/minecraftforge/client/event/sound/PlaySoundEvent;)V": None,
    "(Lnet/minecraftforge/client/event/sound/PlaySoundSourceEvent;)V": None,

    "(Lnet/minecraftforge/event/entity/living/LivingFallEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/living/LivingSpawnEvent$CheckSpawn;)V": None,
    "(Lnet/minecraftforge/event/entity/living/LivingEvent$LivingUpdateEvent;)V": None,

    "(Lnet/minecraftforge/event/entity/living/LivingDeathEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/living/LivingDropsEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerDropsEvent;)V": None,

    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$Clone;)V": None,
    "(Lnet/minecraftforge/event/entity/EntityEvent$EntityConstructing;)V": None,
    "(Lnet/minecraftforge/fml/common/gameevent/PlayerEvent$PlayerRespawnEvent;)V": None,
    "(Lnet/minecraftforge/fml/common/gameevent/PlayerEvent$PlayerChangedDimensionEvent;)V": None,
    "(Lnet/minecraftforge/event/world/BlockEvent$HarvestDropsEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/AttackEntityEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/ArrowNockEvent;)V": None,

    "(Lnet/minecraftforge/event/world/BlockEvent$NeighborNotifyEvent;)V": None,

    "(Lnet/minecraftforge/event/entity/player/PlayerInteractEvent$LeftClickBlock;)V": None,
    "(Lnet/minecraftforge/fml/common/gameevent/InputEvent$KeyInputEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$StartTracking;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerDestroyItemEvent;)V": None,
    "(Lnet/minecraftforge/client/event/MouseEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$BreakSpeed;)V": None,
    "(Lnet/minecraftforge/event/world/BlockEvent$BreakEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerInteractEvent$RightClickBlock;)V": None,

    "(Lnet/minecraftforge/event/AnvilUpdateEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/living/EnderTeleportEvent;)V": None,
    "(Lnet/minecraftforge/client/event/FOVUpdateEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$NameFormat;)V": None,

    "(Lnet/minecraftforge/event/entity/living/ZombieEvent$SummonAidEvent;)V": None,

    "(Lnet/minecraftforge/event/world/ChunkDataEvent$Save;)V": None,
    "(Lnet/minecraftforge/event/world/ChunkDataEvent$Load;)V": None,
    "(Lnet/minecraftforge/event/world/WorldEvent$Unload;)V": None,
    "(Lnet/minecraftforge/event/world/WorldEvent$Save;)V": None,
    "(Lnet/minecraftforge/event/world/WorldEvent$Load;)V": None,

    "(Lnet/minecraftforge/fml/common/gameevent/PlayerEvent$PlayerLoggedInEvent;)V": None,
    "(Lnet/minecraftforge/fml/common/network/FMLNetworkEvent$ClientDisconnectionFromServerEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/EntityJoinWorldEvent;)V": None,
}


@builtin_handler.bind_class_annotation("net/minecraftforge/fml/common/eventhandler/SubscribeEvent")
def subscribeToEvent(cls, obj: jvm.api.AbstractMethod, args):
    if not obj.access & 0x0008:  # Is it static?
        return

    if not isinstance(obj, jvm.api.AbstractMethod):
        raise ValueError(obj)

    modname = shared.CURRENT_EVENT_SUB

    if obj.signature in EventType2EventStage:
        # print("annotating", cls, obj, args)

        e = EventType2EventStage[obj.signature]

        if e is None: return

        event_name, arg_producer, target_id = e

        def handle_event(*a):
            shared.CURRENT_EVENT_SUB = modname

            try:
                obj.invoke(*arg_producer(a))

            except StackCollectingException as error:
                if shared.IS_CLIENT:
                    import mcpython.common.state.LoadingExceptionViewState
                    traceback.print_exc()
                    print(error.format_exception())
                    mcpython.common.state.LoadingExceptionViewState.error_occur(error.format_exception())

                raise LoadingInterruptException

            except:
                if shared.IS_CLIENT:
                    import mcpython.common.state.LoadingExceptionViewState
                    traceback.print_exc()
                    mcpython.common.state.LoadingExceptionViewState.error_occur(traceback.format_exc())

                raise LoadingInterruptException

        if target_id == 0:
            shared.mod_loader(shared.CURRENT_EVENT_SUB, event_name)(handle_event)
        elif target_id == 1:
            PUBLIC_EVENT_BUS.subscribe(event_name, handle_event)

    elif obj.signature.startswith("(Lnet/minecraftforge"):
        print(f"[FML][WARN] mod '{modname}' is subscribing for event '{obj.signature}', which is not arrival in data set")
        EventType2EventStage[obj.signature] = None

