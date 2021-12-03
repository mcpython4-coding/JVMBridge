from jvm.natives import bind_native, bind_annotation


@bind_annotation("org/spongepowered/asm/mixin/Mixin")
@bind_annotation("org/spongepowered/asm/mixin/gen/Accessor")
@bind_annotation("org/spongepowered/asm/mixin/injection/Inject")
@bind_annotation("org/spongepowered/asm/mixin/gen/Invoker")
@bind_annotation("org/spongepowered/asm/mixin/injection/Redirect")
@bind_annotation("org/spongepowered/asm/mixin/injection/ModifyConstant")
@bind_annotation("org/spongepowered/asm/mixin/injection/ModifyArg")
@bind_annotation("org/spongepowered/asm/mixin/Overwrite")
@bind_annotation("org/spongepowered/asm/mixin/Shadow")
@bind_annotation("org/spongepowered/asm/mixin/Mutable")
@bind_annotation("org/spongepowered/asm/mixin/injection/ModifyVariable")
@bind_annotation("org/spongepowered/asm/mixin/Unique")
def annotate_mixin(*args):
    pass


class MixinBootstrap:
    @staticmethod
    @bind_native("org/spongepowered/asm/launch/MixinBootstrap", "<init>()V")
    def init(method, stack, this):
        pass

