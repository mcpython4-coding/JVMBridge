from jvm.natives import bind_native, bind_annotation


@bind_annotation("org/spongepowered/asm/mixin/Mixin")
@bind_annotation("org/spongepowered/asm/mixin/gen/Accessor")
@bind_annotation("org/spongepowered/asm/mixin/injection/Inject")
@bind_annotation("org/spongepowered/asm/mixin/gen/Invoker")
@bind_annotation("org/spongepowered/asm/mixin/injection/Redirect")
@bind_annotation("org/spongepowered/asm/mixin/injection/ModifyConstant")
def annotate_mixin(*args):
    pass

