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
import threading

from mcpython import shared
from jvm.Java import NativeClass, native


class Thread(NativeClass):
    NAME = "java/lang/Thread"

    @native("<init>", "(Ljava/lang/Runnable;)V")
    def init(self, instance, target):
        instance.thread = threading.Thread(target=target)

    @native("setName", "(Ljava/lang/String;)V")
    def setName(self, instance, name):
        instance.thread.name = name

    @native("setDaemon", "(Z)V")
    def setDaemon(self, instance, is_daemon):
        pass

    @native("start", "()V")
    def start(self, instance):
        instance.thread.start()

    @native("currentThread", "()Ljava/lang/Thread;", static=True)
    def currentThread(self):
        instance = self.create_instance()
        instance.thread = threading.currentThread()
        return instance

    @native("getThreadGroup", "()Ljava/lang/ThreadGroup;")
    def getThreadGroup(self, instance: threading.Thread):
        pass

    @native("getContextClassLoader", "()Ljava/lang/ClassLoader;")
    def getContextClassLoader(self, *_):
        return self.vm

    @native("getStackTrace", "()[Ljava/lang/StackTraceElement;")
    def getStackTrace(self, *_):
        return []
