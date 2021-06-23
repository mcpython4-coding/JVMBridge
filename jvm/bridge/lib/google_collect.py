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
import re
import time

from mcpython import shared
from jvm.Java import NativeClass, native
from jvm.JavaExceptionStack import StackCollectingException


class HashMultiMap(NativeClass):
    NAME = "com/google/common/collect/HashMultimap"

    @native("create", "()Lcom/google/common/collect/HashMultimap;")
    def create(self):
        instance = self.create_instance()
        return instance


class Lists(NativeClass):
    NAME = "com/google/common/collect/Lists"

    @native("newArrayList", "()Ljava/util/ArrayList;")
    def create(self):
        instance = self.vm.get_class(
            "java/util/ArrayList", version=self.internal_version
        ).create_instance()
        return instance

    @native("newArrayList", "([Ljava/lang/Object;)Ljava/util/ArrayList;")
    def newArrayList(self, array):
        return array

    @native("newLinkedList", "()Ljava/util/LinkedList;")
    def newLinkedList(self):
        return []


class Maps(NativeClass):
    NAME = "com/google/common/collect/Maps"

    @native("newHashMap", "()Ljava/util/HashMap;")
    def create(self):
        instance = self.vm.get_class(
            "java/util/HashMap", version=self.internal_version
        ).create_instance()
        return instance

    @native("newHashMap", "(Ljava/util/Map;)Ljava/util/HashMap;")
    def copyHashMap(self, instance):
        return instance.copy()

    @native("newEnumMap", "(Ljava/util/Map;)Ljava/util/EnumMap;")
    def newEnumMap(self, base_map):
        return base_map

    @native("newTreeMap", "()Ljava/util/TreeMap;")
    def newTreeMap(self):
        return {}

    @native("newIdentityHashMap", "()Ljava/util/IdentityHashMap;")
    def newIdentityHashMap(self, *_):
        return {}


class ImmutableList(NativeClass):
    NAME = "com/google/common/collect/ImmutableList"

    def create_instance(self):
        instance = super().create_instance()
        instance.underlying_tuple = None
        return instance

    @native(
        "of",
        "(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;[Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;",
    )
    def of(self, *stuff):
        instance = self.create_instance()
        instance.underlying_tuple = stuff[:-1] + tuple(stuff[-1])
        return instance

    @native(
        "of",
        "(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;",
    )
    def of_2(self, *stuff):
        instance = self.create_instance()
        instance.underlying_tuple = stuff
        return instance

    @native("of", "(Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;")
    def of_3(self, obj):
        instance = self.create_instance()
        instance.underlying_tuple = obj,
        return instance

    @native("of",
            "(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;")
    def of_4(self, *stuff):
        instance = self.create_instance()
        instance.underlying_tuple = stuff
        return instance

    @native("copyOf", "([Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;")
    def copyOf(self, array):
        instance = self.create_instance()
        instance.underlying_tuple = tuple(array)
        return instance

    @native("iterator", "()Lcom/google/common/collect/UnmodifiableIterator;")
    def iterator(self, instance):
        return instance

    @native("size", "()I")
    def size(self, instance):
        return len(instance) if isinstance(instance, tuple) else len(instance.underlying_tuple)


class ImmutableMap(NativeClass):
    NAME = "com/google/common/collect/ImmutableMap"

    def create_instance(self):
        return {}

    @native("builder", "()Lcom/google/common/collect/ImmutableMap$Builder;")
    def builder(self):
        return self.vm.get_class(
            "com/google/common/collect/ImmutableMap$Builder",
            version=self.internal_version,
        ).create_instance()

    @native(
        "of",
        "(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableMap;",
    )
    def of(self, *stuff):
        return self.create_instance()

    @native("get", "(Ljava/lang/Object;)Ljava/lang/Object;")
    def get(self, instance, key):
        return None if key not in instance else instance[key]


class ImmutableMap__Builder(NativeClass):
    NAME = "com/google/common/collect/ImmutableMap$Builder"

    def create_instance(self):
        return {}

    @native("<init>", "()V")
    def init(self, *_):
        pass

    @native(
        "putAll", "(Ljava/util/Map;)Lcom/google/common/collect/ImmutableMap$Builder;"
    )
    def putAll(self, instance, data):
        instance.update(data)
        return instance

    @native(
        "put",
        "(Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableMap$Builder;",
    )
    def put(self, instance, key, value):
        instance[key] = value
        return instance

    @native("build", "()Lcom/google/common/collect/ImmutableMap;")
    def build(self, instance):
        return instance  # todo: make immutable


class ImmutableMultimap(NativeClass):
    NAME = "com/google/common/collect/ImmutableMultimap"

    @native("builder", "()Lcom/google/common/collect/ImmutableMultimap$Builder;")
    def builder(self):
        return self.vm.get_class(
            "com/google/common/collect/ImmutableMultimap$Builder",
            version=self.internal_version,
        ).create_instance()


class ImmutableMultimap__Builder(NativeClass):
    NAME = "com/google/common/collect/ImmutableMultimap$Builder"

    @native(
        "put",
        "(Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableMultimap$Builder;",
    )
    def put(self, instance, key, value):
        return instance

    @native("build", "()Lcom/google/common/collect/ImmutableMultimap;")
    def build(self, instance):
        return self.vm.get_class(
            "com/google/common/collect/ImmutableMultimap", version=self.internal_version
        ).create_instance()


class MutableClassToInstanceMap(NativeClass):
    NAME = "com/google/common/collect/MutableClassToInstanceMap"

    @native("create", "()Lcom/google/common/collect/MutableClassToInstanceMap;")
    def create(self):
        return self.create_instance()

    @native("containsKey", "(Ljava/lang/Object;)Z")
    def containsKey(self, instance, key):
        return False

    @native("putInstance", "(Ljava/lang/Class;Ljava/lang/Object;)Ljava/lang/Object;")
    def putInstance(self, instance, cls, obj):
        return obj


class Preconditions(NativeClass):
    NAME = "com/google/common/base/Preconditions"

    @native("checkNotNull", "(Ljava/lang/Object;)Ljava/lang/Object;")
    def checkNotNull(self, obj):
        if obj is None:
            raise StackCollectingException("expected non-null, got null")
        return obj

    @native("checkNotNull", "(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;")
    def checkNotNull2(self, obj, msg):
        if obj is None:
            raise StackCollectingException(
                "expected non-null, got null, message: " + str(msg)
            )
        return obj

    @native("checkArgument", "(Z)V")
    def checkArgument(self, value):
        if not value:
            raise StackCollectingException("expected true, got false")

    @native("checkArgument", "(ZLjava/lang/Object;)V")
    def checkArgument2(self, value, obj):
        if not value:
            raise StackCollectingException(f"expected true, got false, message: {obj}")

    @native("checkState", "(ZLjava/lang/Object;)V")
    def checkState(self, value, obj):
        if not value:
            raise StackCollectingException(f"expected true, got false, message: {obj}")


class ClassToInstanceMap(NativeClass):
    NAME = "com/google/common/collect/ClassToInstanceMap"

    @native("containsKey", "(Ljava/lang/Object;)Z")
    def containsKey(self, instance, key):
        return False

    @native("putInstance", "(Ljava/lang/Class;Ljava/lang/Object;)Ljava/lang/Object;")
    def putInstance(self, instance, cls, obj):
        return obj


class CharMatcher(NativeClass):
    NAME = "com/google/common/base/CharMatcher"

    @native(
        "forPredicate",
        "(Lcom/google/common/base/Predicate;)Lcom/google/common/base/CharMatcher;",
    )
    def forPredicate(self, *_):
        pass

    @native("anyOf", "(Ljava/lang/CharSequence;)Lcom/google/common/base/CharMatcher;")
    def anyOf(self, *_):
        pass

    @native(
        "or",
        "(Lcom/google/common/base/CharMatcher;)Lcom/google/common/base/CharMatcher;",
    )
    def or_(self, *_):
        pass


class Strings(NativeClass):
    NAME = "com/google/common/base/Strings"

    @native("isNullOrEmpty", "(Ljava/lang/String;)Z")
    def isNullOrEmpty(self, string: str):
        return int(string is None or len(string) == 0)

    @native("nullToEmpty", "(Ljava/lang/String;)Ljava/lang/String;")
    def nullToEmpty(self, instance):
        return instance if instance is not None else ""


class ImmutableSet(NativeClass):
    NAME = "com/google/common/collect/ImmutableSet"

    @native(
        "copyOf", "(Ljava/util/Collection;)Lcom/google/common/collect/ImmutableSet;"
    )
    def copyOf(self, collection):
        obj = self.create_instance()

        try:
            obj.underlying = (
                set(collection)
                if not hasattr(collection, "get_class")
                or not hasattr(collection.get_class(), "iter_over_instance")
                else set(collection.get_class().iter_over_instance(collection))
            )
        except TypeError:
            raise NotImplementedError(f"object {collection} seems not iterable!")

        return obj

    @native(
        "of",
        "(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Lcom/google/common/collect/ImmutableSet;",
    )
    def of(self, *elements):
        return set(elements)

    @native("of",
            "(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;[Ljava/lang/Object;)Lcom/google/common/collect/ImmutableSet;")
    def of2(self, *elements):
        return set(elements[:-1]) | set(elements[-1])

    @native("builder", "()Lcom/google/common/collect/ImmutableSet$Builder;")
    def builder(self):
        return set()


class ImmutableSet__Builder(NativeClass):
    NAME = "com/google/common/collect/ImmutableSet$Builder"

    @native(
        "add", "(Ljava/lang/Object;)Lcom/google/common/collect/ImmutableSet$Builder;"
    )
    def add(self, instance, obj):
        instance.add(obj)
        return instance

    @native("build", "()Lcom/google/common/collect/ImmutableSet;")
    def build(self, instance):
        return instance  # todo: make immutable


class BiMap(NativeClass):
    NAME = "com/google/common/collect/BiMap"

    @native("put", "(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;")
    def put(self, instance, key, value):
        instance[key] = value
        return value


class Joiner(NativeClass):
    NAME = "com/google/common/base/Joiner"

    @native("on", "(Ljava/lang/String;)Lcom/google/common/base/Joiner;")
    def on(self, string: str):
        return self.create_instance()


class ArrayListMultimap(NativeClass):
    NAME = "com/google/common/collect/ArrayListMultimap"

    @native("create", "()Lcom/google/common/collect/ArrayListMultimap;")
    def create(self):
        return self.create_instance()


class Sets(NativeClass):
    NAME = "com/google/common/collect/Sets"

    @native("newHashSet", "()Ljava/util/HashSet;")
    def newHashSet(self, *_):
        return set()


class Multimaps(NativeClass):
    NAME = "com/google/common/collect/Multimaps"

    @native(
        "newListMultimap",
        "(Ljava/util/Map;Lcom/google/common/base/Supplier;)Lcom/google/common/collect/ListMultimap;",
    )
    def newListMultimap(self, *_):
        return {}


class ImmutableBiMap(NativeClass):
    NAME = "com/google/common/collect/ImmutableBiMap"

    def create_instance(self):
        return {}

    @native("of", "()Lcom/google/common/collect/ImmutableBiMap;")
    def of(self, *_):
        return {}


class Verify(NativeClass):
    NAME = "com/google/common/base/Verify"

    @native("verify", "(Z)V")
    def verify(self, value):
        if not value:
            raise StackCollectingException("expected true, got false")


class Stopwatch(NativeClass):
    NAME = "com/google/common/base/Stopwatch"

    @native("createStarted", "()Lcom/google/common/base/Stopwatch;")
    def createStarted(self):
        instance = self.create_instance()
        instance.time_started = time.time()
        return instance

    @native("createUnstarted", "()Lcom/google/common/base/Stopwatch;")
    def createUnstarted(self, *_):
        instance = self.create_instance()
        instance.time_started = -1
        return instance

    @native("elapsed", "(Ljava/util/concurrent/TimeUnit;)J")
    def elapsed(self, instance, unit):
        return time.time() - instance.time_started


class LinkedListMultimap(NativeClass):
    NAME = "com/google/common/collect/LinkedListMultimap"

    @native("create", "()Lcom/google/common/collect/LinkedListMultimap;")
    def create(self, *_):
        return self.create_instance()


class AbstractInvocationHandler(NativeClass):
    NAME = "com/google/common/reflect/AbstractInvocationHandler"

    @native("<init>", "()V")
    def init(self, instance):
        pass


class Charsets(NativeClass):
    NAME = "com/google/common/base/Charsets"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "UTF_8": "utf-8"
        })


class Resources(NativeClass):
    NAME = "com/google/common/io/Resources"

    @native("toString", "(Ljava/net/URL;Ljava/nio/charset/Charset;)Ljava/lang/String;")
    def toString(self, url, charset):
        return url


class TypeToken(NativeClass):
    NAME = "com/google/common/reflect/TypeToken"

    @native("<init>", "()V")
    def init(self, *_):
        pass

    @native("getType", "()Ljava/lang/reflect/Type;")
    def getType(self, instance):
        pass


class Predicates(NativeClass):
    NAME = "com/google/common/base/Predicates"

    @native("equalTo", "(Ljava/lang/Object;)Lcom/google/common/base/Predicate;")
    def equalTo(self, obj):
        return lambda e: e == obj

    @native("not", "(Lcom/google/common/base/Predicate;)Lcom/google/common/base/Predicate;")
    def not_(self, predicate):
        return lambda e: not predicate(e)


class MapMaker(NativeClass):
    NAME = "com/google/common/collect/MapMaker"

    @native("<init>", "()V")
    def init(self, instance):
        instance.level = 0
        instance.has_weak_keys = False

    @native("concurrencyLevel", "(I)Lcom/google/common/collect/MapMaker;")
    def concurrencyLevel(self, instance, level):
        instance.level = level
        return instance

    @native("weakKeys", "()Lcom/google/common/collect/MapMaker;")
    def weakKeys(self, instance):
        instance.has_weak_keys = True
        return instance

    @native("makeMap", "()Ljava/util/concurrent/ConcurrentMap;")
    def makeMap(self, instance):
        return {}


class Beta(NativeClass):
    NAME = "com/google/common/annotations/Beta"

    def on_annotate(self, cls, args):
        pass


class HashBasedTable(NativeClass):
    NAME = "com/google/common/collect/HashBasedTable"

    def create_instance(self):
        return {}

    @native("create", "()Lcom/google/common/collect/HashBasedTable;")
    def create(self, *_):
        return {}


class CaseFormat(NativeClass):
    NAME = "com/google/common/base/CaseFormat"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "LOWER_CAMEL": 0,
            "UPPER_UNDERSCORE": 1,
        })
        self.camel2score = re.compile(r'(?<!^)(?=[A-Z])')
        self.converters = {
            (0, 1): lambda string: self.camel2score.sub("_", string).upper(),
            (1, 0): lambda string: "".join(word.title() for word in string.split('_'))
        }

    @native("converterTo", "(Lcom/google/common/base/CaseFormat;)Lcom/google/common/base/Converter;")
    def converterTo(self, start, end):
        return self.converters[(start, end)]

