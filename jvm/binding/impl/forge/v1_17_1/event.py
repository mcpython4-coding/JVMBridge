import traceback

import jvm.builtinwrapper
import jvm.api
from mcpython import shared
from mcpython.common.mod.util import LoadingInterruptException
from mcpython.engine.event.EventHandler import PUBLIC_EVENT_BUS

from jvm.JavaExceptionStack import StackCollectingException


CLIENT_TICK_EVENT = jvm.api.vm.get_class("net/minecraftforge/event/TickEvent$ClientTickEvent", version="1.16.5").create_instance()
CLIENT_TICK_EVENT.fields["wasCanceled"] = 0

RENDER_TICK_EVENT = jvm.api.vm.get_class("net/minecraftforge/event/TickEvent$RenderTickEvent", version="1.16.5").create_instance()


EventType2EventStage = {
    "(Lnet/minecraftforge/fml/event/lifecycle/FMLCommonSetupEvent;)V": ("stage:mod:init", lambda e: [None], 0),
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$PotionShiftEvent;)V": ("stage:post", lambda e: [None], 0),
    "(Lnet/minecraftforge/fml/event/lifecycle/FMLClientSetupEvent;)V": ("stage:client:work", lambda e: [None], 0),
    "(Lnet/minecraftforge/client/event/ColorHandlerEvent$Item;)V": ("stage:item:load", lambda e: [None], 0),
    "(Lnet/minecraftforge/client/event/ColorHandlerEvent$Block;)V": ("stage:block:load", lambda e: [None], 0),
    "(Lnet/minecraftforge/event/RegistryEvent$Register;)V": ("stage:combined_factory:blocks", lambda e: [None], 0),
    "(Lnet/minecraftforge/client/event/ModelRegistryEvent;)V": ("stage:model:model_create", lambda e: [None], 0),
    "(Lnet/minecraftforge/client/event/TextureStitchEvent$Pre;)V": ("stage:textureatlas:prepare", lambda e: [None], 0),
    "(Lnet/minecraftforge/client/event/TextureStitchEvent$Post;)V": ("stage:textureatlas:prepare", lambda e: [None], 0),
    "(Lnet/minecraftforge/fml/config/ModConfig$Loading;)V": ("stage:mod:config:load", lambda e: [None], 0),
    "(Lnet/minecraftforge/fml/config/ModConfig$Reloading;)V": ("stage:mod:config:load", lambda e: [None], 0),
    "(Lnet/minecraftforge/fml/config/ModConfig$ModConfigEvent;)V": ("stage:mod:config:load", lambda e: [None], 0),
    "(Lnet/minecraftforge/event/AddReloadListenerEvent;)V": ("stage:post", lambda e: [None], 0),
    "(Lnet/minecraftforge/fml/event/lifecycle/FMLLoadCompleteEvent;)V": ("stage:post", lambda e: [None], 0),
    "(Lnet/minecraftforge/event/RegisterCommandsEvent;)V": ("stage:commands", lambda e: [None], 0),
    "(Lnet/minecraftforge/event/world/BiomeLoadingEvent;)V": ("stage:worldgen:biomes", lambda e: [None], 0),
    "(Lnet/minecraftforge/client/event/ModelBakeEvent;)V": ("stage:model:model_bake", lambda e: [None], 0),

    "(Lnet/minecraftforge/event/TagsUpdatedEvent;)V": None,
    "(Lnet/minecraftforge/client/event/RecipesUpdatedEvent;)V": None,
    "(Lnet/minecraftforge/event/LootTableLoadEvent;)V": None,
    "(Lnet/minecraftforge/fml/network/NetworkEvent$ClientCustomPayloadEvent;)V": None,
    "(Lnet/minecraftforge/fml/network/NetworkEvent$ServerCustomPayloadEvent;)V": None,

    "(Lnet/minecraftforge/client/event/RenderGameOverlayEvent;)V": None,  # ("render:draw:2d:overlay", lambda e: [None], 1),
    "(Lnet/minecraftforge/client/event/RenderGameOverlayEvent$Pre;)V": None,  # ("render:draw:2d:overlay", lambda e: [None], 1),
    "(Lnet/minecraftforge/client/event/RenderGameOverlayEvent$Post;)V": None,  # ("render:draw:2d:overlay", lambda e: [None], 1),
    "(Lnet/minecraftforge/client/event/RenderWorldLastEvent;)V": None,  # ("render:draw:post:cleanup", lambda e: [None], 1),
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$DrawScreenEvent$Post;)V": None,  # ("render:draw:2d:overlay", lambda e: [None], 1),
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$DrawScreenEvent;)V": None,  # ("render:draw:2d:overlay", lambda e: [None], 1),
    "(Lnet/minecraftforge/client/event/GuiContainerEvent$DrawForeground;)V": None,  # ("render:draw:2d:overlay", lambda e: [None], 1),
    "(Lnet/minecraftforge/client/event/RenderTooltipEvent$PostText;)V": None,  # ("render:draw:2d:overlay", lambda e: [None], 1),
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$DrawScreenEvent$Pre;)V": None,

    "(Lnet/minecraftforge/event/TickEvent$ServerTickEvent;)V": ("tickhandler:general", lambda e: [None], 1),
    "(Lnet/minecraftforge/event/TickEvent$RenderTickEvent;)V": ("tickhandler:general", lambda e: [RENDER_TICK_EVENT], 1),
    "(Lnet/minecraftforge/event/TickEvent$PlayerTickEvent;)V": ("tickhandler:general", lambda e: [None], 1),
    "(Lnet/minecraftforge/event/TickEvent$ClientTickEvent;)V": ("tickhandler:general", lambda e: [CLIENT_TICK_EVENT], 1),
    "(Lnet/minecraftforge/event/TickEvent$WorldTickEvent;)V": ("tickhandler:general", lambda e: [None], 1),

    "(Lnet/minecraftforge/client/event/InputEvent$MouseInputEvent;)V": None,
    "(Lnet/minecraftforge/client/event/InputUpdateEvent;)V": None,
    "(Lnet/minecraftforge/client/event/InputEvent$KeyInputEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerInteractEvent$RightClickBlock;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerInteractEvent$LeftClickBlock;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerInteractEvent$LeftClickEmpty;)V": None,
    "(Lnet/minecraftforge/client/event/InputEvent$MouseScrollEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerInteractEvent$RightClickItem;)V": None,
    "(Lnet/minecraftforge/event/entity/player/AttackEntityEvent;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$MouseDragEvent$Pre;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$MouseScrollEvent$Pre;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$MouseClickedEvent;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$MouseReleasedEvent;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$KeyboardCharTypedEvent;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$KeyboardKeyPressedEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerInteractEvent;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$MouseClickedEvent$Pre;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$StartTracking;)V": None,

    "(Lnet/minecraftforge/event/world/BlockEvent$EntityPlaceEvent;)V": None,
    "(Lnet/minecraftforge/event/world/BlockEvent$BreakEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/living/LivingDropsEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/living/LootingLevelEvent;)V": None,

    "(Lnet/minecraftforge/client/event/DrawHighlightEvent$HighlightBlock;)V": None,

    "(Lnet/minecraftforge/event/entity/player/ItemTooltipEvent;)V": None,
    "(Lnet/minecraftforge/client/event/RenderTooltipEvent$Pre;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$PlayerLoggedInEvent;)V": None,
    "(Lnet/minecraftforge/client/event/RenderPlayerEvent;)V": None,
    "(Lnet/minecraftforge/client/event/RenderPlayerEvent$Pre;)V": None,
    "(Lnet/minecraftforge/client/event/RenderPlayerEvent$Post;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$Clone;)V": None,
    "(Lnet/minecraftforge/event/entity/living/BabyEntitySpawnEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/living/LivingDeathEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/living/LivingEvent$LivingUpdateEvent;)V": None,
    "(Lnet/minecraftforge/client/event/GuiOpenEvent;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$InitGuiEvent$Post;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$InitGuiEvent$Pre;)V": None,
    "(Lnet/minecraftforge/client/event/ClientPlayerNetworkEvent$LoggedOutEvent;)V": None,
    "(Lnet/minecraftforge/client/event/GuiScreenEvent$InitGuiEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/EntityJoinWorldEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$PlayerLoggedOutEvent;)V": None,
    "(Lnet/minecraftforge/client/event/ClientChatReceivedEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerContainerEvent$Open;)V": None,
    "(Lnet/minecraftforge/event/entity/player/EntityItemPickupEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$ItemSmeltedEvent;)V": None,
    "(Lnet/minecraftforge/client/event/EntityViewRenderEvent$FogDensity;)V": None,
    "(Lnet/minecraftforge/client/event/EntityViewRenderEvent$FogColors;)V": None,

    "(Lnet/minecraftforge/client/event/ParticleFactoryRegisterEvent;)V": None,
    "(Lnet/minecraftforge/event/AttachCapabilitiesEvent;)V": None,
    "(Lnet/minecraftforge/fml/event/lifecycle/InterModEnqueueEvent;)V": None,
    "(Lnet/minecraftforge/fml/event/lifecycle/GatherDataEvent;)V": None,
    "(Lnet/minecraftforge/event/RegistryEvent$MissingMappings;)V": None,

    "(Lnet/minecraftforge/event/world/BlockEvent$CropGrowEvent$Post;)V": None,
    "(Lnet/minecraftforge/event/world/SaplingGrowTreeEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerSleepInBedEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$HarvestCheck;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$BreakSpeed;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$ItemCraftedEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerEvent$PlayerRespawnEvent;)V": None,
    "(Lnet/minecraftforge/event/entity/player/PlayerXpEvent$PickupXp;)V": None,

    "(Lnet/minecraftforge/event/world/WorldEvent$Load;)V": None,
    "(Lnet/minecraftforge/event/world/ChunkEvent$Load;)V": None,
    "(Lnet/minecraftforge/fml/event/server/FMLServerStartingEvent;)V": None,
    "(Lnet/minecraftforge/fml/event/server/FMLServerStoppedEvent;)V": None,
    "(Lnet/minecraftforge/fml/event/server/FMLServerStoppingEvent;)V": None,
    "(Lnet/minecraftforge/event/world/WorldEvent$Save;)V": None,
    "(Lnet/minecraftforge/event/world/WorldEvent$Unload;)V": None,
    "(Lnet/minecraftforge/fml/event/server/FMLServerStartedEvent;)V": None,
    "(Lnet/minecraftforge/client/event/ClientPlayerNetworkEvent$LoggedInEvent;)V": None,
    "(Lnet/minecraftforge/event/world/ChunkDataEvent$Save;)V": None,
    "(Lnet/minecraftforge/event/world/ChunkDataEvent$Load;)V": None,
    "(Lnet/minecraftforge/fml/event/server/FMLServerAboutToStartEvent;)V": None,
    "(Lnet/minecraftforge/event/world/ChunkEvent$Unload;)V": None,
}


@jvm.builtinwrapper.handler.bind_class_annotation("net/minecraftforge/eventbus/api/SubscribeEvent", "1.17.1")
@jvm.builtinwrapper.handler.bind_class_annotation("net/minecraftforge/eventbus/api/SubscribeEvent", "1.16.5")
def subscribeToEvent(cls, obj, args):
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
                    import mcpython.client.state.LoadingExceptionViewState
                    traceback.print_exc()
                    print(error.format_exception())
                    mcpython.client.state.LoadingExceptionViewState.error_occur(error.format_exception())

                raise LoadingInterruptException

            except:
                if shared.IS_CLIENT:
                    import mcpython.client.state.LoadingExceptionViewState
                    traceback.print_exc()
                    mcpython.client.state.LoadingExceptionViewState.error_occur(traceback.format_exc())

                raise LoadingInterruptException

        if target_id == 0:
            shared.mod_loader(shared.CURRENT_EVENT_SUB, event_name)(handle_event)
        elif target_id == 1:
            PUBLIC_EVENT_BUS.subscribe(event_name, handle_event)

    elif obj.signature.startswith("(Lnet/minecraftforge"):
        print(f"[FML][WARN] mod '{modname}' is subscribing for event {obj.signature}, which is not arrival in data set")
        EventType2EventStage[obj.signature] = None

