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
import traceback

from mcpython import shared, logger
from jvm.Java import NativeClass, native, JavaMethod, AbstractJavaClass
from jvm.JavaExceptionStack import StackCollectingException


class LocalCapture(NativeClass):
    NAME = "org/spongepowered/asm/mixin/injection/callback/LocalCapture"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {
                "CAPTURE_FAILSOFT": "org/spongepowered/asm/mixin/injection/callback/LocalCapture::CAPTURE_FAILSOFT",
                "CAPTURE_FAILHARD": "org/spongepowered/asm/mixin/injection/callback/LocalCapture::CAPTURE_FAILHARD",
            }
        )


class At__Shift(NativeClass):
    NAME = "org/spongepowered/asm/mixin/injection/At$Shift"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update(
            {"AFTER": "org/spongepowered/asm/mixin/injection/At$Shift::AFTER", "BY": "org/spongepowered/asm/mixin/injection/At$Shift::BY", "BEFORE": "org/spongepowered/asm/mixin/injection/At$Shift::BEFORE"}
        )


class Mixin(NativeClass):
    NAME = "org/spongepowered/asm/mixin/Mixin"

    def on_annotate(self, cls, args):
        try:
            cls.mixin_target = cls.vm.get_class(args[0][1].data[0].data[1][1:-1])
        except StackCollectingException as e:
            print(e.format_exception())
        except:
            traceback.print_exc()


class Invoker(NativeClass):
    NAME = "org/spongepowered/asm/mixin/gen/Invoker"

    def on_annotate(self, method: JavaMethod, args):
        """
        Mixin processor for an Invoker mixin
        Will inject a new method into the target class wrapping the target method
        """
        try:
            if len(args) == 0:
                if not method.name.startswith("invoke"):
                    logger.println(f"[MIXIN][INVOKER][FATAL] failed to invoke {method} as no args where provided")
                    return
                target_method_name = method.name.removeprefix("invoke")
                target_method_name = target_method_name[0].lower() + target_method_name[1:]
                target_method_name = shared.CURRENT_REF_MAP["mappings"][method.class_file.name].setdefault(target_method_name, target_method_name).split("(")[0]
            else:
                target_method_name = shared.CURRENT_REF_MAP["mappings"][method.class_file.name].setdefault(args[0][1].data, args[0][1].data).split("(")[0]

            target_cls: AbstractJavaClass = method.class_file.mixin_target
            override_method = target_cls.get_method(target_method_name, method.signature)

            logger.println(f"[MIXIN][INJECT] injecting into class {target_cls} method '{method.name}{method.signature}' wrapping '{args[0][1] if len(args) > 0 else 'unspecified'}/{target_method_name}{method.signature}'")

            m = lambda *a: override_method(*a)

            native(method.name, method.signature)(m)

            target_cls.inject_method(method.name, method.signature, m)
            method.class_file.methods[(method.name, method.signature)] = m
        except StackCollectingException as e:
            print(e.format_exception())
        except:
            logger.print_exception(f"during annotating {method} with {args}")


class Accessor(NativeClass):
    NAME = "org/spongepowered/asm/mixin/gen/Accessor"

    def on_annotate(self, method: JavaMethod, args):
        """
        Mixin process for an Accessor mixin
        """
        try:
            target_cls: AbstractJavaClass = method.class_file.mixin_target
            target_attribute_name = method.name.removeprefix("get").removeprefix("set")

            if not target_attribute_name.isupper():
                target_attribute_name = target_attribute_name[0].lower() + target_attribute_name[1:]

            target_attribute_name = shared.CURRENT_REF_MAP["mappings"].setdefault(method.class_file.name, {}).setdefault(target_attribute_name, target_attribute_name).split(":")[0]

            if method.name.startswith("get"):
                m = lambda *instance: instance[0].fields[target_attribute_name] if instance else target_cls.get_static_attribute(target_attribute_name)
            else:
                def m(*v):
                    if len(v) == 1:
                        target_cls.set_static_attribute(target_attribute_name, v[0])
                    else:
                        v[0].fields[target_attribute_name] = v[1]

            logger.println(f"[MIXIN][INJECT] injecting attribute accessor into {target_cls.name} accessing '{target_attribute_name}' via '{method.name}{method.signature}'")

            native(method.name, method.signature)(m)

            target_cls.inject_method(method.name, method.signature, m)
            method.class_file.methods[(method.name, method.signature)] = m

        except StackCollectingException as e:
            print(e.format_exception())
        except:
            traceback.print_exc()


class Overwrite(NativeClass):
    NAME = "org/spongepowered/asm/mixin/Overwrite"

    def on_annotate(self, method, args):
        if not hasattr(method.class_file, "mixin_target"):
            logger.println(f"[MIXIN][OVERWRITE][ERROR] failed to attach mixin to {method}; super class was not annotated correctly!")
            return

        try:
            target_cls: AbstractJavaClass = method.class_file.mixin_target

            m = lambda *args: method(*args)

            logger.println(
                f"[MIXIN][INJECT] injecting override into {target_cls.name} at '{method.name}{method.signature}'")

            native(method.name, method.signature)(m)

            target_cls.inject_method(method.name, method.signature, m)
            method.class_file.methods[(method.name, method.signature)] = m

        except StackCollectingException as e:
            print(e.format_exception())
        except:
            traceback.print_exc()


class Inject(NativeClass):
    NAME = "org/spongepowered/asm/mixin/injection/Inject"

    # this requires runtime bytecode modification of python functions, so NO
    def on_annotate(self, cls, args):
        pass


class ModifyArg(NativeClass):
    NAME = "org/spongepowered/asm/mixin/injection/ModifyArg"

    # todo: do something about this
    def on_annotate(self, cls, args):
        pass


class Shadow(NativeClass):
    NAME = "org/spongepowered/asm/mixin/Shadow"

    # todo: implement this
    def on_annotate(self, cls, args):
        pass


class ModifyVariable(NativeClass):
    NAME = "org/spongepowered/asm/mixin/injection/ModifyVariable"

    # todo: implement
    def on_annotate(self, cls, args):
        pass


class Unique(NativeClass):
    NAME = "org/spongepowered/asm/mixin/Unique"

    # todo: implement
    def on_annotate(self, cls, args):
        pass


class ModifyConstant(NativeClass):
    NAME = "org/spongepowered/asm/mixin/injection/ModifyConstant"

    # todo: implement
    def on_annotate(self, cls, args):
        pass


class Redirect(NativeClass):
    NAME = "org/spongepowered/asm/mixin/injection/Redirect"

    def on_annotate(self, cls, args):
        pass  # todo: implement


class Mutable(NativeClass):
    NAME = "org/spongepowered/asm/mixin/Mutable"


    def on_annotate(self, cls, args):
        pass  # todo: implement
