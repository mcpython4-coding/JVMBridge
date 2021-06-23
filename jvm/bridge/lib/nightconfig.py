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


class CommentedFileConfig(NativeClass):
    NAME = "com/electronwill/nightconfig/core/file/CommentedFileConfig"

    @native(
        "builder",
        "(Ljava/nio/file/Path;)Lcom/electronwill/nightconfig/core/file/CommentedFileConfigBuilder;",
    )
    def builder(self, path):
        return self.vm.get_class(
            "com/electronwill/nightconfig/core/file/CommentedFileConfigBuilder",
            version=self.internal_version,
        ).create_instance()

    @native("load", "()V")
    def load(self, instance):
        pass


class CommentedFileConfigBuilder(NativeClass):
    NAME = "com/electronwill/nightconfig/core/file/CommentedFileConfigBuilder"

    @native("sync", "()Lcom/electronwill/nightconfig/core/file/GenericBuilder;")
    def sync(self, instance):
        return self.vm.get_class(
            "com/electronwill/nightconfig/core/file/GenericBuilder",
            version=self.internal_version,
        ).create_instance()

    @native("load", "()V")
    def load(self, instance):
        pass

    @native("get", "(Ljava/lang/String;)Ljava/lang/Object;")
    def get(self, *_):
        pass

    @native("set", "(Ljava/lang/String;Ljava/lang/Object;)Ljava/lang/Object;")
    def set(self, *_):
        pass

    @native("getComment", "(Ljava/lang/String;)Ljava/lang/String;")
    def getComment(self, *_):
        return ""

    @native("setComment", "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;")
    def setComment(self, *_):
        return ""

    @native("valueMap", "()Ljava/util/Map;")
    def valueMap(self, *_):
        return {}

    @native("commentMap", "()Ljava/util/Map;")
    def commentMap(self, *_):
        return {}


class GenericBuilder(NativeClass):
    NAME = "com/electronwill/nightconfig/core/file/GenericBuilder"

    @native("autosave", "()Lcom/electronwill/nightconfig/core/file/GenericBuilder;")
    def autosave(self, instance):
        return instance

    @native(
        "writingMode",
        "(Lcom/electronwill/nightconfig/core/io/WritingMode;)Lcom/electronwill/nightconfig/core/file/GenericBuilder;",
    )
    def writingMode(self, instance, mode):
        return instance

    @native("build", "()Lcom/electronwill/nightconfig/core/file/FileConfig;")
    def build(self, *_):
        return self.vm.get_class(
            "com/electronwill/nightconfig/core/file/CommentedFileConfigBuilder",
            version=self.internal_version,
        ).create_instance()


class WritingMode(NativeClass):
    NAME = "com/electronwill/nightconfig/core/io/WritingMode"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "REPLACE": 0,
            }
        )


class CommentedConfig(NativeClass):
    NAME = "com/electronwill/nightconfig/core/CommentedConfig"

    @native("get", "(Ljava/lang/String;)Ljava/lang/Object;")
    def get(self, *_):
        pass

    @native("inMemory", "()Lcom/electronwill/nightconfig/core/CommentedConfig;")
    def inMemory(self, *_):
        pass

    @native("set", "(Ljava/lang/String;Ljava/lang/Object;)Ljava/lang/Object;")
    def set(self, *_):
        pass

    @native("getComment", "(Ljava/lang/String;)Ljava/lang/String;")
    def getComment(self, *_):
        pass

    @native("setComment", "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;")
    def setComment(self, *_):
        pass

    @native("of",
            "(Ljava/util/function/Supplier;Lcom/electronwill/nightconfig/core/ConfigFormat;)Lcom/electronwill/nightconfig/core/CommentedConfig;", static=True)
    def of(self, supplier, format):
        return self.create_instance()

    @native("valueMap", "()Ljava/util/Map;")
    def valueMap(self, *_):
        return {}

    @native("commentMap", "()Ljava/util/Map;")
    def commentMap(self, *_):
        return {}

    @native("add", "(Ljava/lang/String;Ljava/lang/Object;)Z")
    def add(self, instance, key, value):
        return 1


class Config(NativeClass):
    NAME = "com/electronwill/nightconfig/core/Config"

    @native("getDefaultMapCreator", "(ZZ)Ljava/util/function/Supplier;")
    def getDefaultMapCreator(self, *_):
        pass


class TomlFormat(NativeClass):
    NAME = "com/electronwill/nightconfig/toml/TomlFormat"

    @native("instance", "()Lcom/electronwill/nightconfig/toml/TomlFormat;")
    def instance(self, *_):
        pass


class TomlWriter(NativeClass):
    NAME = "com/electronwill/nightconfig/toml/TomlWriter"

    @native("<init>", "()V")
    def init(self, *_):
        pass

    @native("write",
            "(Lcom/electronwill/nightconfig/core/UnmodifiableConfig;Ljava/io/File;Lcom/electronwill/nightconfig/core/io/WritingMode;)V")
    def write(self, instance, config, file, mode):
        pass


class EnumGetMethod(NativeClass):
    NAME = "com/electronwill/nightconfig/core/EnumGetMethod"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "NAME_IGNORECASE": 0
        })


class InMemoryCommentedFormat(NativeClass):
    NAME = "com/electronwill/nightconfig/core/InMemoryCommentedFormat"

    @native("defaultInstance", "()Lcom/electronwill/nightconfig/core/InMemoryCommentedFormat;")
    def defaultInstance(self, *_):
        return self.create_instance()

    @native("createConfig", "(Ljava/util/function/Supplier;)Lcom/electronwill/nightconfig/core/CommentedConfig;")
    def createConfig(self, instance, supplier):
        return self.vm.get_class("com/electronwill/nightconfig/core/CommentedConfig").create_instance()
