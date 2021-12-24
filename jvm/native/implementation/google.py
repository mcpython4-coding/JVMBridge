import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.natives import bind_native, bind_annotation
from jvm.natives import NativeClassInstance


@bind_annotation("com/google/gson/annotations/JsonAdapter")
@bind_annotation("com/google/common/annotations/VisibleForTesting")
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
    @bind_native("com/google/common/collect/ImmutableList", "builder()Lcom/google/common/collect/ImmutableList$Builder;")
    @bind_native("com/google/common/collect/ImmutableList", "of(Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;")
    @bind_native("com/google/common/collect/ImmutableList", "of(Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;")
    @bind_native("com/google/common/collect/ImmutableList", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;")
    @bind_native("com/google/common/collect/ImmutableList", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;[Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;")
    async def create(method, stack, *args):
        args = list(args)
        if args and isinstance(args[-1], list):
            args += args.pop(-1)

        return await (await method.get_parent_class().create_instance()).init("([Ljava/lang/Object;)V", args)

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableList$Builder", "<init>()V")
    def initEmpty(method, stack, this):
        this.underlying = []

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableList$Builder", "add(Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList$Builder;")
    @bind_native("com/google/common/collect/ImmutableList", "add(Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList$Builder;")
    def addObject(method, stack, this, obj):
        this.underlying.append(obj)
        return this

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableList$Builder", "addAll(Ljava/lang/Iterable;)Lcom/google/common/collect/ImmutableList$Builder;")
    @bind_native("com/google/common/collect/ImmutableList", "addAll(Ljava/lang/Iterable;)Lcom/google/common/collect/ImmutableList$Builder;")
    def addAll(method, stack, this, obj):
        if isinstance(obj, NativeClassInstance):
            this.underlying += obj.underlying
        else:
            this.underlying += obj
        return this

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableList$Builder", "build()Lcom/google/common/collect/ImmutableList;")
    @bind_native("com/google/common/collect/ImmutableList", "build()Lcom/google/common/collect/ImmutableList;")
    def buildList(method, stack, this):
        return tuple(this.underlying)

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableList", "<init>([Ljava/lang/Object;)V")
    def init(method, stack, this, data: list):
        this.underlying = data

    @staticmethod
    @bind_native("com/google/common/collect/Lists", "newArrayList()Ljava/util/ArrayList;")
    async def createArrayList(method, stack):
        return await (await (await stack.vm.get_class("java/util/ArrayList")).create_instance()).init("()V")

    @staticmethod
    @bind_native("com/google/common/collect/Lists", "newArrayList([Ljava/lang/Object;)Ljava/util/ArrayList;")
    async def createArrayListFromArray(method, stack, array):
        obj = await (await (await stack.vm.get_class("java/util/ArrayList")).create_instance()).init("()V")
        obj.underlying += array
        return obj

    @staticmethod
    @bind_native("java/util/ArrayList", "<init>()V")
    def init(method, stack, this):
        this.underlying = []


class MapLike:
    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableMap;")
    async def create(method, stack, *pairs):
        return await  (await method.get_parent_class().create_instance()).init("(Ljava/util/Map;)V", {pairs[2*i]: pairs[2*i + 1] for i in range(len(pairs) // 2)})

    @staticmethod
    @bind_native("com/google/common/collect/BiMap", "<init>()V")
    @bind_native("com/google/common/collect/ImmutableMap", "<init>()V")
    def init(method, stack, this):
        this.underlying = {}

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap", "<init>(Ljava/util/Map;)V")
    def init(method, stack, this, data: dict):
        this.underlying = data.copy()

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap", "builder()Lcom/google/common/collect/ImmutableMap$Builder;")
    async def builder(method, stack):
        obj = (await method.get_parent_class().create_instance())
        obj.underlying = {}
        return obj

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap$Builder", "put(Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableMap$Builder;")
    @bind_native("com/google/common/collect/ImmutableMap", "put(Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableMap$Builder;")
    @bind_native("com/google/common/collect/ImmutableMap", "put(Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableMap")
    @bind_native("com/google/common/collect/BiMap", "put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;")
    def put(method, stack, this, key, value):
        this.underlying[key] = value
        return this

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap", "putAll(Ljava/util/Map;)Lcom/google/common/collect/ImmutableMap$Builder;")
    def putAll(method, stack, this, data):
        this.underlying.update(data.underlying)
        return this

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableMap$Builder", "build()Lcom/google/common/collect/ImmutableMap;")
    @bind_native("com/google/common/collect/ImmutableMap", "build()Lcom/google/common/collect/ImmutableMap;")
    def build(method, stack, this):
        return this

    @staticmethod
    @bind_native("com/google/common/collect/HashMultimap", "<init>()V")
    def init(method, stack, this):
        this.underlying = {}

    @staticmethod
    @bind_native("com/google/common/collect/Maps", "newEnumMap(Ljava/util/Map;)Ljava/util/EnumMap;")
    async def map2enumMap(method, stack, map_obj):
        instance = (await (await stack.vm.get_class("java/util/EnumMap")).create_instance())
        instance.underlying = map_obj.underlying
        return instance

    @staticmethod
    @bind_native("com/google/common/collect/Maps", "newTreeMap()Ljava/util/TreeMap;")
    @bind_native("com/google/common/collect/Maps", "newHashMap()Ljava/util/HashMap;")
    @bind_native("com/google/common/collect/Maps", "newIdentityHashMap()Ljava/util/IdentityHashMap;")
    @bind_native("com/google/common/collect/HashMultimap", "create()Lcom/google/common/collect/HashMultimap;")
    async def createMap(method, stack):
        return await (await (await stack.vm.get_class(method.signature.split(")")[-1][1:-1])).create_instance()).init("()V")


class SetLike:
    @staticmethod
    @bind_native("com/google/common/collect/ImmutableSet", "builder()Lcom/google/common/collect/ImmutableSet$Builder;")
    def initImmutableSet(method, stack, this):
        this.underlying = {}

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableSet", "add(Ljava/lang/Object;)Lcom/google/common/collect/ImmutableSet$Builder;")
    def addImmutableSet(method, stack, this, obj):
        this.underlying.add(obj)
        return this

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableSet", "build()Lcom/google/common/collect/ImmutableSet;")
    def buildImmutableSet(method, stack, this):
        return this

    @staticmethod
    @bind_native("com/google/common/collect/Sets", "newHashSet()Ljava/util/HashSet;")
    async def newHashSet(method, stack):
        return await (await (await stack.vm.get_class("java/util/HashSet")).create_instance()).init("()V")

    @staticmethod
    @bind_native("com/google/common/collect/Sets", "newHashSet([Ljava/lang/Object;)Ljava/util/HashSet;")
    async def newHashSet(method, stack, array):
        obj = await (await (await stack.vm.get_class("java/util/HashSet")).create_instance()).init("()V")
        obj.underlying |= set(array)
        return obj

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableSet", "of()Lcom/google/common/collect/ImmutableSet;")
    async def createImmutableEmpty(method, stack):
        return await (await method.get_parent_class().create_instance()).init("()V")

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableSet", "<init>()V")
    def initImmutableSet(method, stack, this):
        this.underlying = set()
