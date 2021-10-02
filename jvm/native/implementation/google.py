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


class ListLike:
    @staticmethod
    @bind_native("com/google/common/collect/ImmutableList", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;")
    def create(method, stack, *args):
        return method.get_class().create_instance().init("([Ljava/lang/Object;)V", list(args))

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableList", "<init>([Ljava/lang/Object;)V")
    def init(method, stack, this, data: list):
        this.underlying = data

    @staticmethod
    @bind_native("com/google/common/collect/Lists", "newArrayList()Ljava/util/ArrayList;")
    def createArrayList(method, stack):
        return method.get_class().create_instance().init("()V")

    @staticmethod
    @bind_native("com/google/common/collect/Lists", "<init>()V")
    def init(method, stack, this):
        this.underlying = []


class MapLike:
    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableMap;")
    def create(method, stack, *pairs):
        return method.get_class().create_instance().init("(Ljava/util/Map;)V", {pairs[2*i]: pairs[2*i + 1] for i in range(len(pairs) // 2)})

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap", "<init>(Ljava/util/Map;)V")
    def init(method, stack, this, data: list):
        this.underlying = data

    @staticmethod
    @bind_native("com/google/common/collect/Maps", "newEnumMap(Ljava/util/Map;)Ljava/util/EnumMap;")
    def map2enumMap(method, stack, map_obj):
        instance = stack.vm.get_class("java/util/EnumMap").create_instance()
        instance.underlying = map_obj.underlying
        return instance
