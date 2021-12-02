import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.natives import bind_native, bind_annotation


@bind_annotation("com/google/gson/annotations/JsonAdapter")
def unusedAnnotation(method, stack, target, args):
    pass


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
    @bind_native("com/google/common/collect/ImmutableList", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;[Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;")
    def create(method, stack, *args):
        args = list(args)
        if isinstance(args[-1], list):
            args += args.pop(-1)

        return method.get_class().create_instance().init("([Ljava/lang/Object;)V", args)

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableList", "<init>([Ljava/lang/Object;)V")
    def init(method, stack, this, data: list):
        this.underlying = data

    @staticmethod
    @bind_native("com/google/common/collect/Lists", "newArrayList()Ljava/util/ArrayList;")
    def createArrayList(method, stack):
        return stack.vm.get_class("java/util/ArrayList").create_instance().init("()V")

    @staticmethod
    @bind_native("com/google/common/collect/Lists", "newArrayList([Ljava/lang/Object;)Ljava/util/ArrayList;")
    def createArrayListFromArray(method, stack, array):
        obj = stack.vm.get_class("java/util/ArrayList").create_instance().init("()V")
        obj.underlying += array
        return obj

    @staticmethod
    @bind_native("java/util/ArrayList", "<init>()V")
    def init(method, stack, this):
        this.underlying = []


class MapLike:
    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableMap;")
    def create(method, stack, *pairs):
        return method.get_class().create_instance().init("(Ljava/util/Map;)V", {pairs[2*i]: pairs[2*i + 1] for i in range(len(pairs) // 2)})

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap", "<init>(Ljava/util/Map;)V")
    def init(method, stack, this, data: dict):
        this.underlying = data.copy()

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap", "builder()Lcom/google/common/collect/ImmutableMap$Builder;")
    def builder(method, stack):
        obj = method.get_class().create_instance()
        obj.underlying = {}
        return obj

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap$Builder", "put(Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableMap$Builder;")
    @bind_native("com/google/common/collect/ImmutableMap", "put(Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableMap$Builder;")
    def put(method, stack, this, key, value):
        this.underlying[key] = value
        return this

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap$Builder", "build()Lcom/google/common/collect/ImmutableMap;")
    def build(method, stack, this):
        return this

    @staticmethod
    @bind_native("com/google/common/collect/HashMultimap", "<init>()V")
    def init(method, stack, this):
        this.underlying = {}

    @staticmethod
    @bind_native("com/google/common/collect/Maps", "newEnumMap(Ljava/util/Map;)Ljava/util/EnumMap;")
    def map2enumMap(method, stack, map_obj):
        instance = stack.vm.get_class("java/util/EnumMap").create_instance()
        instance.underlying = map_obj.underlying
        return instance

    @staticmethod
    @bind_native("com/google/common/collect/Maps", "newTreeMap()Ljava/util/TreeMap;")
    @bind_native("com/google/common/collect/Maps", "newHashMap()Ljava/util/HashMap;")
    @bind_native("com/google/common/collect/HashMultimap", "create()Lcom/google/common/collect/HashMultimap;")
    def createMap(method, stack):
        return stack.vm.get_class(method.signature.split(")")[-1][1:-1]).create_instance().init("()V")


class SetLike:
    @staticmethod
    @bind_native("com/google/common/collect/Sets", "newHashSet()Ljava/util/HashSet;")
    def newHashSet(method, stack):
        return stack.vm.get_class("java/util/HashSet").create_instance().init("()V")

    @staticmethod
    @bind_native("com/google/common/collect/Sets", "newHashSet([Ljava/lang/Object;)Ljava/util/HashSet;")
    def newHashSet(method, stack, array):
        obj = stack.vm.get_class("java/util/HashSet").create_instance().init("()V")
        obj.underlying |= set(array)
        return obj
