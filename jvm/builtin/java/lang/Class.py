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
import mcpython.engine.ResourceLoader
from mcpython.engine import logger
from jvm.Java import AbstractJavaClass, NativeClass, native, JavaBytecodeClass


class Class(NativeClass):
    NAME = "java/lang/Class"

    @native("isInstance", "(Ljava/lang/Object;)Z")
    def isInstance(self, instance, obj):
        return obj.get_class().is_subclass_of(instance.name)

    @native("getInterfaces", "()[Ljava/lang/Class;")
    def getInterfaces(self, instance):
        return [interface() for interface in instance.interfaces]

    @native("forName", "(Ljava/lang/String;)Ljava/lang/Class;")
    def forName(self, name: str):
        return self.vm.get_class(name, version=self.internal_version)

    @native("newInstance", "()Ljava/lang/Object;")
    def newInstance(self, cls):
        return cls.create_instance()

    @native("desiredAssertionStatus", "()Z")
    def desiredAssertionStatus(self, *_):
        return 0

    @native("getSimpleName", "()Ljava/lang/String;")
    def getSimpleName(self, instance):
        return instance.name

    @native("getResourceAsStream", "(Ljava/lang/String;)Ljava/io/InputStream;")
    def getResourceAsStream(self, instance, path: str):
        return mcpython.engine.ResourceLoader.read_raw(path.removeprefix("/"))

    @native("getDeclaredFields", "()[Ljava/lang/reflect/Field;")
    def getDeclaredFields(self, instance):
        if isinstance(instance, NativeClass):
            # logger.println(
            #     f"[WARN] from NativeImplementation: NativeImplementation.getDeclaredFields on {instance} is unsafe"
            # )
            return list(
                instance.get_dynamic_field_keys()
                | set(instance.exposed_attributes.keys())
            )

        return list(instance.fields.values())

    @native("getDeclaredMethods", "()[Ljava/lang/reflect/Method;")
    def getDeclaredMethods(self, instance):
        if isinstance(instance, NativeClass):
            # logger.println(
            #     f"[WARN] from NativeImplementation: NativeImplementation.getDeclaredMethods on {instance} is unsafe"
            # )
            return list(instance.exposed_methods.values())

        return list(instance.methods.values())

    @native("getSuperclass", "()Ljava/lang/Class;")
    def getSuperclass(self, instance: AbstractJavaClass):
        if isinstance(instance, NativeClass):
            # logger.println(
            #     f"[WARN] from NativeImplementation: NativeImplementation.getSuperClass on {instance} is unsafe"
            # )
            pass

        # If parent is None, parent is java/lang/Object, which is listed as None
        return instance.parent() if instance.parent is not None else None

    @native("getName", "()Ljava/lang/String;")
    def getName(self, instance):
        return instance.name

    @native("getClassLoader", "()Ljava/lang/ClassLoader;")
    def getClassLoader(self, instance: AbstractJavaClass):
        return instance.vm

    @native("forName", "(Ljava/lang/String;ZLjava/lang/ClassLoader;)Ljava/lang/Class;")
    def forName(self, name: str, init, loader):
        return (loader if loader is not None else self.vm).get_class(name)

    @native("getComponentType", "()Ljava/lang/Class;")
    def getComponentType(self, instance):
        return self.vm.get_class("java/lang/Object")

    @native("getResource", "(Ljava/lang/String;)Ljava/net/URL;")
    def getResource(self, instance, name):
        return name

    @native("forName", "(Ljava/lang/String;)Ljava/lang/Class;")
    def forName2(self, name: str):
        return self.vm.get_class(name, version=self.internal_version)

    @native("getConstructor", "([Ljava/lang/Class;)Ljava/lang/reflect/Constructor;")
    def getConstructor(self, instance, signature):
        return instance  # todo: implement

    @native("isAssignableFrom", "(Ljava/lang/Class;)Z")
    def isAssignableFrom(self, instance, cls):
        return False

    @native("getFields", "()[Ljava/lang/reflect/Field;")
    def getFields(self, instance):
        return instance.get_dynamic_field_keys()

    @native("getAnnotation", "(Ljava/lang/Class;)Ljava/lang/annotation/Annotation;")
    def getAnnotation(self, instance):
        if instance is None: return None
        if not isinstance(instance, JavaBytecodeClass): return

        return instance.attributes["RuntimeVisibleAnnotations"]

    @native("getField", "(Ljava/lang/String;)Ljava/lang/reflect/Field;")
    def getField(self, instance, name: str):
        pass

    @native("getMethod", "(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;")
    def getMethod(self, instance, name, signature):
        pass

    @native("getCanonicalName", "()Ljava/lang/String;")
    def getCanonicalName(self, instance):
        return instance.name

    @native("getDeclaredMethod", "(Ljava/lang/String;[Ljava/lang/Class;)Ljava/lang/reflect/Method;")
    def getDeclaredMethod(self, *_):
        return []
