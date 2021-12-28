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

import typing

import jvm.JavaVM
import jvm.logging
from mcpython.common.mod.ModLoader import ModContainer

from jvm.ClassAdressing import IClassAccessor

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
import jvm.natives


FORGE_VERSION_NUMBER_TO_MC = {
    37: "1.17.1",
    36: "1.16.5",
    35: "1.16.5",
    34: "1.16.5",
    33: "1.17.1",
    32: "1.16.5",
    31: "1.17.1",
    30: "1.17.1",
    29: "1.17.1",
    28: "1.17.1",
    26: "1.17.1",
    25: "1.17.1",
    14: "1.17.1",
    "1.12.2": "1.12.2",
}


jvm.natives.manager.vm = jvm.api.vm
jvm.natives.manager.load_files()


class McpythonResourceLookup(IClassAccessor):
    async def try_access_resource(self, path: str) -> typing.Optional[bytes]:
        try:
            return await mcpython.engine.ResourceLoader.read_raw(path)
        except (FileNotFoundError, KeyError, NameError):
            pass


# Replace java bytecode loader with ResourceLoader's lookup system
jvm.api.vm.add_accessor(McpythonResourceLookup())

# jvm.Java.info = lambda text: logger.println("[JAVA][INFO]", text)
jvm.logging.warn = lambda text: logger.println("[JAVA][WARN]", text)


class JavaMod(mcpython.common.mod.Mod.Mod):
    runtime = jvm.Runtime.Runtime()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loader_version = 0

    def mod_string(self):
        return super().mod_string() + " [JavaFML]"

    async def load_underlying_classes(self):
        """
        Called during mod init for loading the java code from the .jar archives
        """

        try:
            for file in self.resource_access.get_all_entries_in_directory(""):
                if file.endswith(".mixins.json"):
                    logger.println(f"found mixin info file at {file} for mod {self.name}")
                    await self.load_mixin_map(file)

            for file in self.resource_access.get_all_entries_in_directory(""):
                if not file.endswith(".class"):
                    continue

                await self.load_mod_file(file)
        except:
            print(self.container, self.name)
            raise

    async def load_mixin_map(self, file: str):
        """
        Loader for the mixin ref-map data
        Does some smart stuff with the data
        :param file: the file, as reach-able by local access
        """

        data = json.loads((await self.resource_access.read_raw(file)).decode("utf-8"))

        if "refmap" in data:
            refmap = data["refmap"]

            try:
                refmap_data = json.loads((await self.resource_access.read_raw(refmap)).decode("utf-8"))
            except KeyError:
                logger.println("[MIXIN PROCESSOR][FATAL] failed to load refmap")
                return

            shared.CURRENT_REF_MAP = refmap_data
        else:
            shared.CURRENT_REF_MAP = {}

        package = data["package"].replace(".", "/")

        if "mixins" in data:
            for file in data["mixins"]:
                module = package + "/" + file

                shared.CURRENT_EVENT_SUB = self.name

                try:
                    await (await jvm.api.vm.load_class(module, version=FORGE_VERSION_NUMBER_TO_MC[self.loader_version])).prepare_use()
                except StackCollectingException as e:
                    if shared.IS_CLIENT:
                        shared.window.set_caption("JavaFML JVM error (during loading mixins)")

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
                        pyglet.app.exit()
                        print("closing")

                    raise LoadingInterruptException from None

    async def load_mod_file(self, file: str):
        """
        Loads a given file which the local resource access can reach
        :param file: the file
        """

        import mcpython.common.state.LoadingExceptionViewState

        cls = file.split(".")[0]
        try:
            # make sure that this is set!
            shared.CURRENT_EVENT_SUB = self.name

            if self.loader_version not in FORGE_VERSION_NUMBER_TO_MC:
                version = "1.17.1"
            else:
                version = FORGE_VERSION_NUMBER_TO_MC[self.loader_version]

            await jvm.api.vm.load_class(cls, version=version)

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
                if shared.IS_CLIENT:
                    shared.window.close()

                pyglet.app.exit()
                print("closing")

            raise LoadingInterruptException from None


class JavaModLoader(AbstractModLoaderInstance):
    """
    This is an example extension point for the mod loader
    It binds the java bytecode loader framework together with its bridges to mcpython mod loader
    """

    async def on_select(self):
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

    async def on_select(self):
        data = json.loads(
            (await self.container.resource_access.read_raw("mcmod.info")).decode("utf-8")
        )

        self.raw_data = data
        self.load_from_data(data)

    def load_from_data(self, data: typing.Union[list, dict]):
        if isinstance(data, dict):
            return self.parse_entry(data)

        for entry in data:
            self.parse_entry(entry)

    def parse_entry(self, entry: dict):
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
