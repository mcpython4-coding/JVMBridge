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
from mcpython import shared, logger
from jvm.Java import NativeClass, native
import json


class Gson(NativeClass):
    NAME = "com/google/gson/Gson"

    @native("<init>", "()V")
    def init(self, *_):
        pass

    @native("fromJson", "(Ljava/lang/String;Ljava/lang/reflect/Type;)Ljava/lang/Object;")
    def fromJson(self, instance, text, target_type):
        if target_type is not None:
            return target_type

        if text == "":
            return []

        try:
            return json.loads(text)
        except json.decoder.JSONDecodeError:
            logger.println(f"[GSON][WARN] failed to decode json data: {text}!")
            return []

    @native("fromJson", "(Ljava/io/Reader;Ljava/lang/reflect/Type;)Ljava/lang/Object;")
    def fromJson2(self, instance, reader, target_type):
        if not hasattr(reader, "read"):
            text = reader.get_class().read_stuff(reader)
        else:
            text = reader.read()

        if target_type is not None:
            return target_type

        if text == "":
            return []

        try:
            return json.loads(text)
        except json.decoder.JSONDecodeError:
            logger.println(f"[GSON][WARN] failed to decode json data: {text}!")
            return []


class GsonBuilder(NativeClass):
    NAME = "com/google/gson/GsonBuilder"

    @native("<init>", "()V")
    def init(self, instance):
        pass

    @native("setPrettyPrinting", "()Lcom/google/gson/GsonBuilder;")
    def setPrettyPrinting(self, instance):
        return instance

    @native("create", "()Lcom/google/gson/Gson;")
    def create(self, instance):
        return self.vm.get_class(
            Gson.NAME, version=self.internal_version
        ).create_instance()

    @native(
        "registerTypeAdapter",
        "(Ljava/lang/reflect/Type;Ljava/lang/Object;)Lcom/google/gson/GsonBuilder;",
    )
    def registerTypeAdapter(self, instance, t, obj):
        return instance

    @native("disableHtmlEscaping", "()Lcom/google/gson/GsonBuilder;")
    def disableHtmlEscaping(self, instance):
        return instance

    @native("serializeNulls", "()Lcom/google/gson/GsonBuilder;")
    def serializeNulls(self, instance):
        return instance

    @native("setLenient", "()Lcom/google/gson/GsonBuilder;")
    def setLenient(self, instance):
        return instance


class JsonAdapter(NativeClass):
    NAME = "com/google/gson/annotations/JsonAdapter"

    def on_annotate(self, cls, args):
        pass


class TypeToken(NativeClass):
    NAME = "com/google/gson/reflect/TypeToken"

    @native("<init>", "()V")
    def init(self, *_):
        pass

    @native("getType", "()Ljava/lang/reflect/Type;")
    def getType(self, *_):
        pass
