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
import json

import jvm.JavaVM
import jvm.logging
from mcpython.common.mod.ModLoader import ModContainer

'''
Integration point to mcpython's mod loader 
Highly depends on code of that stuff, so don't use it without it
'''
import traceback

from mcpython.common.mod.ModLoader import AbstractModLoaderInstance, ModLoader
from mcpython.common.mod.util import LoadingInterruptException
import mcpython.common.mod.Mod
import jvm.Java
import jvm.Runtime
import mcpython.engine.ResourceLoader
import pyglet.app
from mcpython import shared
from mcpython.engine import logger
import jvm.api
from jvm.JavaExceptionStack import StackCollectingException
import jvm.builtinwrapper


FORGE_VERSION_NUMBER_TO_MC = {
    37: "1.17.1",
    36: "1.16.5",
    35: "1.16.5",
    34: "1.16.5",
    32: "1.16.5",
    "1.12.2": "1.12.2",
}


jvm.builtinwrapper.load_default_indexes(mcpython=True)


# Replace java bytecode loader with ResourceLoader's lookup system
jvm.JavaVM.get_bytecode_of_class = (
    lambda file: mcpython.engine.ResourceLoader.read_raw(file.replace(".", "/") + ".class")
)
# jvm.Java.info = lambda text: logger.println("[JAVA][INFO]", text)
jvm.logging.warn = lambda text: logger.println("[JAVA][WARN]", text)


class JavaMod(mcpython.common.mod.Mod.Mod):
    runtime = jvm.Runtime.Runtime()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loader_version = 0

    def mod_string(self):
        return super().mod_string() + " [JavaFML]"

    def load_underlying_classes(self):
        """
        Called during mod init for loading the java code from the .jar archives
        """

        try:
            for file in self.resource_access.get_all_entries_in_directory(""):
                if file.endswith(".mixins.json"):
                    logger.println(f"found mixin info file at {file} for mod {self.name}")
                    self.load_mixin_map(file)

            for file in self.resource_access.get_all_entries_in_directory(""):
                if not file.endswith(".class"):
                    continue

                self.load_mod_file(file)
        except:
            print(self.container, self.name)
            raise

    def load_mixin_map(self, file: str):
        """
        Loader for the mixin ref-map data
        Does some smart stuff with the data
        :param file: the file, as reach-able by local access
        """

        data = json.loads(self.resource_access.read_raw(file).decode("utf-8"))

        refmap = data["refmap"]

        try:
            refmap_data = json.loads(self.resource_access.read_raw(refmap).decode("utf-8"))
        except KeyError:
            logger.println("[MIXIN PROCESSOR][FATAL] failed to load refmap")
            return

        shared.CURRENT_REF_MAP = refmap_data

        package = data["package"].replace(".", "/")

        if "mixins" in data:
            for file in data["mixins"]:
                module = package + "/" + file

                shared.CURRENT_EVENT_SUB = self.name

                jvm.api.vm.load_class(module, version=FORGE_VERSION_NUMBER_TO_MC[self.loader_version]).prepare_use()

    def load_mod_file(self, file: str):
        """
        Loads a given file which the local resource access can reach
        :param file: the file
        """

        import mcpython.common.state.LoadingExceptionViewState

        cls = file.split(".")[0]
        try:
            # make sure that this is set!
            shared.CURRENT_EVENT_SUB = self.name

            jvm.api.vm.load_class(cls, version=FORGE_VERSION_NUMBER_TO_MC[self.loader_version])

        # StackCollectingException is something internal and contains more meta-data than the other exceptions
        except StackCollectingException as e:
            if shared.IS_CLIENT:
                shared.window.set_caption("JavaFML JVM error")

                try:
                    import mcpython.common.state.LoadingExceptionViewState

                    exception = e.format_exception()
                    mcpython.common.state.LoadingExceptionViewState.error_occur(exception)
                    logger.print_exception("raw exception trace")
                    logger.write_into_container(
                        "fatal FML error", exception.split("\n")
                    )
                except:
                    logger.print_exception("error screen error")

            else:
                shared.window.close()
                pyglet.app.exit()
                print("closing")

            raise LoadingInterruptException from None

        # LoadingInterruptException is something we hand over to the underlying stuff
        except LoadingInterruptException:
            raise

        # Any other exception is handled beforehand
        except:
            logger.print_exception("[JAVA][FATAL] fatal class loader exception")

            if shared.IS_CLIENT:
                shared.window.set_caption("JavaFML JVM error")

                try:
                    mcpython.common.state.LoadingExceptionViewState.error_occur(
                        traceback.format_exc()
                    )
                except:
                    logger.print_exception("error screen error")

            else:
                shared.window.close()
                pyglet.app.exit()
                print("closing")

            raise LoadingInterruptException from None


class JavaModLoader(AbstractModLoaderInstance):
    """
    This is an example extension point for the mod loader
    It binds the java bytecode loader framework together with its bridges to mcpython mod loader
    """

    def on_select(self):
        shared.mod_loader.current_container = self.container
        data = self.parent.raw_data

        loader_version = int(
            data["loaderVersion"]
            .removeprefix("[")
            .removesuffix(",)")
            .removesuffix(",]")
            .split(".")[0]
            .split(",")[0]
        )

        mods = {}

        for d in data["mods"]:
            mod = JavaMod(d["modId"], d["version"].split("-")[-1] if "version" in d else (0, 0, 0))
            mod.add_load_default_resources()
            mods[d["modId"]] = mod
            mod.loader_version = loader_version
            mod.resource_access = self.container.resource_access
            mod.container = self.container

            shared.mod_loader(d["modId"], "stage:mod:init")(mod.load_underlying_classes)

        if "dependencies" in data:
            for mod in data["dependencies"]:
                # these are error handlers, they should NOT be here... Some people produce really bad mods!

                if isinstance(mod, dict):
                    logger.println(
                        f"[FML][SEMI FATAL] skipping dependency block {mod} as block is invalid [provided mods: {list(mod.keys())}]"
                    )
                    continue

                if mod not in mods:
                    logger.println(
                        f"[FML][HARD WARN] reference error in dependency block to {mod} [provided: {list(mods.keys())}]"
                    )
                    continue

                try:
                    for d in data["dependencies"][mod]:
                        # search for optional deps
                        if not d["mandatory"]:
                            continue

                        mods[mod].add_dependency(
                            d["modId"] if d["modId"] != "forge" else "minecraft"
                        )
                except:
                    logger.print_exception(
                        "decoding dependency structure", str(mod), data
                    )


class McModInfoLoader(AbstractModLoaderInstance):
    # mcmod.info
    @classmethod
    def match_container_loader(cls, container: ModContainer) -> bool:
        return container.resource_access.is_in_path("mcmod.info")

    def on_select(self):
        data = json.loads(
            self.container.resource_access.read_raw("mcmod.info").decode("utf-8")
        )

        self.raw_data = data
        self.load_from_data(data)

    def load_from_data(self, data: dict):
        for entry in data:
            v = entry["version"].split("-")[-1]
            mod = JavaMod(entry["modid"], tuple(int(e) for e in v.split(".")))
            mod.add_load_default_resources()
            mod.loader_version = entry["mcversion"].split("-")[0]
            mod.resource_access = self.container.resource_access
            mod.container = self.container

            shared.mod_loader(entry["modid"], "stage:mod:init")(mod.load_underlying_classes)


ModLoader.TOML_LOADERS["javafml"] = JavaModLoader
ModLoader.TOML_LOADERS["kotori_scala"] = JavaModLoader
ModLoader.TOML_LOADERS["kotlinforforge"] = JavaModLoader
ModLoader.KNOWN_MOD_LOADERS.append(McModInfoLoader)
