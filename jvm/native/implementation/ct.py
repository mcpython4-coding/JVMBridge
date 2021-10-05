import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.natives import bind_native, bind_annotation


class Annotations:
    @staticmethod
    @bind_annotation("stanhebben/zenscript/annotations/ZenClass")
    @bind_annotation("crafttweaker/annotations/ZenRegister")
    @bind_annotation("stanhebben/zenscript/annotations/ZenMethod")
    @bind_annotation("stanhebben/zenscript/annotations/ZenGetter")
    @bind_annotation("crafttweaker/annotations/BracketHandler")
    @bind_annotation("stanhebben/zenscript/annotations/ZenOperator")
    @bind_annotation("stanhebben/zenscript/annotations/ZenExpansion")
    @bind_annotation("com/blamejared/crafttweaker/api/annotations/ZenRegister")
    @bind_annotation("org/openzen/zencode/java/ZenCodeType$Name")
    @bind_annotation("org/openzen/zencode/java/ZenCodeType$Method")
    def noAnnotationProcessing(method, stack, target, args):
        pass

