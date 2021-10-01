import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.natives import bind_native, bind_annotation


class Suppliers:
    @staticmethod
    @bind_native("com/google/common/base/Suppliers", "memoize(Lcom/google/common/base/Supplier;)Lcom/google/common/base/Supplier;")
    def memoize(method, stack, supplier):
        cache = None
        cache_set = False

        def supply(*args, **kwargs):
            nonlocal cache, cache_set

            if cache_set:
                return cache

            cache = supplier(*args, **kwargs)
            return cache

        return supply

