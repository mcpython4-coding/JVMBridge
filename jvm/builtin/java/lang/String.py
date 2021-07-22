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
from jvm.Java import NativeClass, native
from jvm.JavaExceptionStack import StackCollectingException
from mcpython.engine import logger


class String(NativeClass):
    NAME = "java/lang/String"

    @native("equals", "(Ljava/lang/Object;)Z")
    def equals(self, instance, other):
        return instance == other

    @native("contains", "(Ljava/lang/CharSequence;)Z")
    def contains(self, instance, substring):
        return substring in instance

    @native("split", "(Ljava/lang/String;)[Ljava/lang/String;")
    def split(self, instance, at):
        return instance.split(at)

    @native("valueOf", "(I)Ljava/lang/String;")
    def valueOf(self, value):
        return str(value)

    @native("valueOf", "(Ljava/lang/Object;)Ljava/lang/String;")
    def valueOf2(self, value):
        return str(value)

    @native("toLowerCase", "()Ljava/lang/String;")
    def toLowerCase(self, instance):
        return instance.lower()

    @native("toLowerCase", "(Ljava/util/Locale;)Ljava/lang/String;")
    def toLowerCase2(self, instance, locale):
        return instance.lower()

    @native("format", "(Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/String;")
    def format(self, instance, items):
        try:
            return instance % items
        except TypeError:
            logger.println(f"[FML][WARN] String.format got invalid parameter: {repr(instance)} % {repr(items)}")
            return instance

    @native("trim", "()Ljava/lang/String;")
    def trim(self, instance: str):
        return instance.strip()

    @native("isEmpty", "()Z")
    def isEmpty(self, instance):
        return int(instance == "")

    @native("replaceAll", "(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;")
    def replaceAll(self, instance, before, after):
        return instance.replace(before, after)

    @native("toCharArray", "()[C")
    def toCharArray(self, instance):
        return [ord(e) for e in instance]

    @native("replace", "(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;")
    def replace(self, instance: str, before: str, after: str):
        return instance.replace(before, after, 1)

    @native("replace", "(CC)Ljava/lang/String;")
    def replace2(self, instance: str, before: int, after: int):
        return instance.replace(chr(before), chr(after), 1)

    @native("indexOf", "(I)I")
    def indexOf(self, instance, v: int):
        c = chr(v)
        return instance.index(c) if c in instance else -1

    @native("indexOf", "(Ljava/lang/String;)I")
    def indexOf2(self, instance, substring):
        return instance.index(substring) if substring in instance else -1

    @native("charAt", "(I)C")
    def charAt(self, instance, index):
        return ord(instance[index])

    @native("lastIndexOf", "(I)I")
    def lastIndexOf(self, instance: str, v: int):
        c = chr(v)
        return instance.rindex(c) if c in instance else -1

    @native("substring", "(II)Ljava/lang/String;")
    def substring(self, instance, start, end):
        return instance[start:end]

    @native("substring", "(I)Ljava/lang/String;")
    def substring2(self, instance, start):
        return instance[start:]

    @native("equalsIgnoreCase", "(Ljava/lang/String;)Z")
    def equalsIgnoreCase(self, instance, other):
        return instance.lower() == other.lower()

    @native("length", "()I")
    def length(self, instance):
        return len(instance)

    @native("getBytes", "()[B")
    def getBytes(self, instance):
        return instance.encode("utf-8")


class StringBuilder(NativeClass):
    NAME = "java/lang/StringBuilder"

    @native("<init>", "()V")
    def init(self, instance):
        instance.underlying = []

    @native("append", "(Ljava/lang/String;)Ljava/lang/StringBuilder;")
    def append(self, instance, text):
        if instance is None:
            raise StackCollectingException("NullPointerException: self is null")

        instance.underlying.append(text)
        return instance

    @native("append", "(Z)Ljava/lang/StringBuilder;")
    def append2(self, instance, value):
        if instance is None:
            raise StackCollectingException("NullPointerException: self is null")

        instance.underlying.append(str(value).lower())
        return instance

    @native("append", "(I)Ljava/lang/StringBuilder;")
    def append3(self, instance, value):
        if instance is None:
            raise StackCollectingException("NullPointerException: self is null")

        instance.underlying.append(str(value))
        return instance

    @native("append", "(Ljava/lang/Object;)Ljava/lang/StringBuilder;")
    def append4(self, instance, value):
        if instance is None:
            raise StackCollectingException("NullPointerException: self is null")

        instance.underlying.append(str(value))
        return instance

    @native("append", "(C)Ljava/lang/StringBuilder;")
    def append5(self, instance, c: int):
        if instance is None:
            raise StackCollectingException("NullPointerException: self is null")

        instance.underlying.append(chr(c) if isinstance(c, int) else str(c))
        return instance

    @native("append", "(J)Ljava/lang/StringBuilder;")
    def append6(self, instance, value):
        if instance is None:
            raise StackCollectingException("NullPointerException: self is null")

        instance.underlying.append(str(value))
        return instance

    @native("toString", "()Ljava/lang/String;")
    def toString(self, instance):
        return "".join(instance.underlying)
