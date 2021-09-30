import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.natives import bind_native, bind_annotation


class Annotations:
    @staticmethod
    @bind_annotation("mezz/jei/api/JEIPlugin")
    def noAnnotationProcessing(method, stack, target, args):
        pass

