import asyncio
import collections
import os.path
import re
import threading
import time
import uuid

import typing

import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.Java import JavaMethod
from jvm.JavaExceptionStack import StackCollectingException
from jvm.natives import bind_native, bind_annotation
from jvm.natives import NativeClassInstance
# from mcpython.engine import logger


@bind_annotation("javax/annotation/Nullable")
@bind_annotation("javax/annotation/Nonnull")
@bind_annotation("java/lang/annotation/Target")
@bind_annotation("java/lang/annotation/Retention")
@bind_annotation("java/lang/Deprecated")
@bind_annotation("java/lang/FunctionalInterface")
@bind_annotation("java/lang/SafeVarargs")
@bind_annotation("javax/annotation/ParametersAreNonnullByDefault")
@bind_annotation("javax/annotation/meta/TypeQualifierDefault")
@bind_annotation("javax/annotation/Nonnegative")
@bind_annotation("org/jetbrains/annotations/ApiStatus$Internal")
@bind_annotation("org/jetbrains/annotations/Nullable")
@bind_annotation("org/jetbrains/annotations/NotNull")
@bind_annotation("java/lang/annotation/Inherited")
@bind_annotation("javax/annotation/CheckForNull")
@bind_annotation("javax/annotation/meta/TypeQualifierNickname")
@bind_annotation("org/jetbrains/annotations/ApiStatus$Experimental")
@bind_annotation("org/jetbrains/annotations/ApiStatus$ScheduledForRemoval")
@bind_annotation("org/jetbrains/annotations/ApiStatus$NonExtendable")
@bind_annotation("dev/architectury/injectables/annotations/ExpectPlatform$Transformed")
@bind_annotation("dev/architectury/injectables/annotations/ExpectPlatform")
@bind_annotation("org/jetbrains/annotations/VisibleForTesting")
@bind_annotation("org/jetbrains/annotations/Contract")
@bind_annotation("org/jetbrains/annotations/ApiStatus$OverrideOnly")
@bind_annotation("org/jetbrains/annotations/Debug$Renderer")
@bind_annotation("javax/annotation/concurrent/ThreadSafe")
@bind_annotation("javax/annotation/OverridingMethodsMustInvokeSuper")
@bind_annotation("org/intellij/lang/annotations/Pattern")
def noAnnotation(method, stack, target, args):
    pass


@bind_native("java/lang/Object", "<init>()V")
@bind_native("java/util/Properties", "<init>()V")
@bind_native("java/lang/SecurityManager", "<init>()V")
@bind_native("java/lang/ClassLoader", "<init>()V")
@bind_native("java/lang/ThreadLocal", "initialValue()Ljava/lang/Object;")
@bind_native("java/lang/ClassLoader", "getParent()Ljava/lang/ClassLoader;")
@bind_native("java/lang/annotation/Documented", "onObjectAnnotation(Ljava/lang/Object;Ljava/lang/List;)V")
def noAction(method, stack, this, *args):
    pass


@bind_native("java/lang/Boolean", "valueOf(Z)Ljava/lang/Boolean;")
@bind_native("java/lang/Integer", "valueOf(I)Ljava/lang/Integer;")
@bind_native("java/lang/Boolean", "booleanValue()Z")
@bind_native("java/lang/Integer", "intValue()I")
@bind_native("java/lang/Class", "asSubclass(Ljava/lang/Class;)Ljava/lang/Class;")
@bind_native("java/lang/Double", "valueOf(D)Ljava/lang/Double;")
@bind_native("java/lang/Double", "doubleValue()D")
@bind_native("java/util/Collections", "unmodifiableMap(Ljava/util/Map;)Ljava/util/Map;")
def thisMap(method, stack, this, *_):
    return this


@bind_native("java/lang/Integer", "parseInt(Ljava/lang/String;)I")
def parseToInt(method, stack, value):
    try:
        return int(value)
    except ValueError:
        return 0


@bind_native("java/lang/Integer", "toString(I)Ljava/lang/String;")
def transform2string(method, stack, this):
    return str(this)


class SetLike:
    @staticmethod
    @bind_native("java/util/Set", "<init>()V")
    @bind_native("java/util/HashSet", "<init>()V")
    @bind_native("java/util/LinkedHashSet", "<init>()V")
    @bind_native("java/util/Set", "<init>()V")
    @bind_native("java/util/HashSet", "<init>()V")
    @bind_native("java/util/TreeSet", "<init>(Ljava/util/Comparator;)V")
    def init(method, stack, this, *_):
        this.underlying = set()
        this.max_size = -1

    @staticmethod
    @bind_native("java/util/LinkedHashSet", "<init>(I)V")
    @bind_native("java/util/HashSet", "<init>(I)V")
    def init2(method, stack, this, max_size):
        this.underlying = set()
        this.max_size = max_size

    @staticmethod
    @bind_native("java/util/EnumSet", "<init>(SOURCE)V")
    def init2(method, stack, this, source):
        this.underlying = set(source)
        this.max_size = -1

    @staticmethod
    @bind_native("java/util/HashSet", "add(Ljava/lang/Object;)Z")
    @bind_native("java/util/LinkedHashSet", "add(Ljava/lang/Object;)Z")
    @bind_native("java/util/Set", "add(Ljava/lang/Object;)Z")
    @bind_native("java/util/TreeSet", "add(Ljava/lang/Object;)Z")
    @bind_native("java/util/EnumSet", "add(Ljava/lang/Object;)Z")
    def add(method, stack, this, element):
        if this.max_size != -1 and len(this.underlying) >= this.max_size:
            return False

        this.underlying.add(element)
        return True

    @staticmethod
    @bind_native("java/util/HashSet", "addAll(Ljava/util/Collection;)Z")
    def addAll(method, stack, this, elements):
        this.underlying |= set(elements)  # todo: check max size
        return True

    @staticmethod
    @bind_native("java/util/HashSet", "size()I")
    @bind_native("java/util/LinkedHashSet", "size()I")
    @bind_native("java/util/Set", "size()I")
    @bind_native("java/util/TreeSet", "size()I")
    @bind_native("java/util/EnumSet", "size()I")
    def getSize(stack, this):
        return len(this.underlying)

    @staticmethod
    @bind_native("java/util/HashSet", "iterator()Ljava/util/Iterator;")
    @bind_native("java/util/LinkedHashSet", "iterator()Ljava/util/Iterator;")
    @bind_native("java/util/Set", "iterator()Ljava/util/Iterator;")
    @bind_native("java/util/TreeSet", "iterator()Ljava/util/Iterator;")
    @bind_native("java/util/EnumSet", "iterator()Ljava/util/Iterator;")
    async def iterator(method, stack, this):
        return await (await (await stack.vm.get_class("java/util/Iterator")).create_instance()).init("(ITERABLE)V", list(this.underlying))

    @staticmethod
    @bind_native("java/util/Set", "forEach(Ljava/util/function/Consumer;)V")
    def forEach(method, stack, this, consumer):
        for item in list(this.underlying):
            consumer(item)

    @staticmethod
    @bind_native("java/util/HashSet", "toArray([Ljava/lang/Object;)[Ljava/lang/Object;")
    @bind_native("java/util/LinkedHashSet", "toArray([Ljava/lang/Object;)[Ljava/lang/Object;")
    @bind_native("java/util/Set", "toArray([Ljava/lang/Object;)[Ljava/lang/Object;")
    @bind_native("java/util/TreeSet", "toArray([Ljava/lang/Object;)[Ljava/lang/Object;")
    @bind_native("java/util/EnumSet", "toArray([Ljava/lang/Object;)[Ljava/lang/Object;")
    def toArray(method, stack, this, array: list):
        array.clear()
        array.extend(this.underlying)
        return array

    @staticmethod
    @bind_native("java/util/EnumSet", "allOf(Ljava/lang/Class;)Ljava/util/EnumSet;")
    async def allOf(method, stack, cls: jvm.api.AbstractJavaClass):
        return await (await (await stack.vm.get_class("java/util/EnumSet")).create_instance()).init("(SOURCE)V", await cls.get_enum_values())

    @staticmethod
    @bind_native("java/util/HashSet", "isEmpty()Z")
    @bind_native("java/util/LinkedHashSet", "isEmpty()Z")
    @bind_native("java/util/Set", "isEmpty()Z")
    @bind_native("java/util/TreeSet", "isEmpty()Z")
    @bind_native("java/util/EnumSet", "isEmpty()Z")
    def isEmpty(method, stack, this):
        return len(this.underlying) == 0

    @staticmethod
    @bind_native("java/util/Set", "stream()Ljava/util/stream/Stream;")
    async def stream(method, stack, this):
        obj = await (await (await stack.vm.get_class("java/util/List")).create_instance()).init("()V")
        obj.underlying += list(this.underlying)
        return obj


class ListLike:
    @staticmethod
    @bind_native("java/util/Enumeration", "<init>()V")
    @bind_native("java/util/ArrayList", "<init>()V")
    @bind_native("java/util/List", "<init>()V")
    @bind_native("java/util/concurrent/CopyOnWriteArrayList", "<init>()V")
    def init(method, stack, this):
        this.underlying = list()

    @staticmethod
    @bind_native("java/util/Iterator", "<init>(ITERABLE)V")
    @bind_native("java/util/ArrayList", "<init>(Ljava/util/Collection;)V")
    def initFromIter(method, stack, this, source: list):
        this.underlying = source

    @staticmethod
    @bind_native("java/util/Collections", "singletonList(Ljava/lang/Object;)Ljava/util/List;")
    async def singletonList(method, stack, obj):
        return await (await (await stack.vm.get_class("java/util/Iterator")).create_instance()).init("(ITERABLE)V", [obj])

    @staticmethod
    @bind_native("java/util/Iterator", "hasNext()Z")
    def hasNext(method, stack, this):
        return len(this.underlying) > 0 if this is not None else False

    @staticmethod
    @bind_native("java/util/Iterator", "next()Ljava/lang/Object;")
    def nextElement(method, stack, this):
        return this.underlying.pop(0)

    @staticmethod
    @bind_native("java/util/ArrayList", "add(Ljava/lang/Object;)Z")
    @bind_native("java/util/List", "add(Ljava/lang/Object;)Z")
    @bind_native("java/util/concurrent/CopyOnWriteArrayList", "add(Ljava/lang/Object;)Z")
    def add(method, stack, this, obj):
        if not hasattr(this, "underlying"):
            del this

        this.underlying.append(obj)
        return True

    @staticmethod
    @bind_native("java/util/ArrayList", "add(ILjava/lang/Object;)V")
    def addAt(method, stack, this, index, obj):
        this.underlying.insert(index, obj)

    @staticmethod
    @bind_native("java/util/concurrent/CopyOnWriteArrayList", "size()I")
    @bind_native("java/util/ArrayList", "size()I")
    def size(method, stack, this):
        return len(this.underlying)

    @staticmethod
    @bind_native("java/util/Arrays", "asList([Ljava/lang/Object;)Ljava/util/List;")
    @bind_native("java/util/Collections", "unmodifiableList(Ljava/util/List;)Ljava/util/List;")
    async def asList(method, stack, this):
        obj = await (await (await stack.vm.get_class("java/util/List")).create_instance()).init("()V")

        if isinstance(this, NativeClassInstance):
            obj.underlying = this.underlying
        else:
            obj.underlying = this

        return obj

    @staticmethod
    @bind_native("java/util/List", "iterator()Ljava/util/Iterator;")
    def asIterator(method, stack, this):
        return list(this)

    @staticmethod
    @bind_native("java/util/ArrayList", "clear()V")
    def clearArrayList(method, stack, this):
        this.underlying.clear()

    @staticmethod
    @bind_native("java/util/ArrayList", "get(I)Ljava/lang/Object;")
    def getFrom(method, stack, this, index):
        return this.underlying[index]

    @staticmethod
    @bind_native("com/google/common/collect/ImmutableList", "copyOf([Ljava/lang/Object;)Lcom/google/common/collect/ImmutableList;")
    def copyOf(method, stack, this):
        return this.copy()

    @staticmethod
    @bind_native("java/util/ArrayList", "forEach(Ljava/util/function/Consumer;)V")
    @bind_native("java/util/List", "forEach(Ljava/util/function/Consumer;)V")
    @bind_native("java/util/Collection", "forEach(Ljava/util/function/Consumer;)V")
    def forEach(method, stack, this, consumer):
        for item in this.underlying:
            consumer(item)

    @staticmethod
    @bind_native("java/util/Collections", "emptyList()Ljava/util/List;")
    @bind_native("java/util/List", "of()Ljava/util/List;")
    @bind_native("java/util/List", "of(Ljava/lang/Object;)Ljava/util/List;")
    @bind_native("java/util/List", "of(Ljava/lang/Object;Ljava/lang/Object;)Ljava/util/List;")
    @bind_native("java/util/List", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Ljava/util/List;")
    @bind_native("java/util/List", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Ljava/util/List;")
    @bind_native("java/util/List", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Ljava/util/List;")
    @bind_native("java/util/List", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Ljava/util/List;")
    @bind_native("java/util/List", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Ljava/util/List;")
    @bind_native("java/util/List", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Ljava/util/List;")
    @bind_native("java/util/List", "of(Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;Ljava/lang/Object;)Ljava/util/List;")
    async def fromVaryingSize(method, stack, *args):
        obj = await (await method.get_parent_class().create_instance()).init("()V")
        obj.underlying += args
        return obj

    @staticmethod
    @bind_native("java/util/List", "of([Ljava/lang/Object;)Ljava/util/List;")
    async def fromArray(method, stack, array):
        obj = await (await method.get_parent_class().create_instance()).init("()V")
        obj.underlying += array
        return obj

    @staticmethod
    @bind_native("java/util/Arrays", "stream([Ljava/lang/Object;)Ljava/util/stream/Stream;")
    async def array2stream(method, stack, array):
        return await (await (await stack.vm.get_class("java/util/stream/Stream")).create_instance()).init("(ARRAY)V", array)

    @staticmethod
    @bind_native("java/util/ArrayList", "stream()Ljava/util/stream/Stream;")
    async def arrayList2stream(method, stack, array):
        return await (await (await stack.vm.get_class("java/util/stream/Stream")).create_instance()).init("(ARRAY)V", array.underlying)

    @staticmethod
    @bind_native("java/util/Collection", "stream()Ljava/util/stream/Stream;")
    @bind_native("java/util/List", "stream()Ljava/util/stream/Stream;")
    async def collection2stream(method, stack, this):
        return await (await (await stack.vm.get_class("java/util/stream/Stream")).create_instance()).init("(ARRAY)V", this.underlying)


class MapLike:
    @staticmethod
    @bind_native("java/util/Map", "entry(Ljava/lang/Object;Ljava/lang/Object;)Ljava/util/Map$Entry;")
    def createMapEntry(method, stack, key, value):
        return key, value

    @staticmethod
    @bind_native("java/util/Map$Entry", "getKey()Ljava/lang/Object;")
    def getKey(method, stack, this):
        return this[0]

    @staticmethod
    @bind_native("java/util/Map$Entry", "getValue()Ljava/lang/Object;")
    def getValue(method, stack, this):
        return this[1]

    @staticmethod
    @bind_native("java/util/Map", "copyOf(Ljava/util/Map;)Ljava/util/Map;")
    async def copyOf(method, stack, other):
        obj = await (await method.get_parent_class().create_instance()).init("()V")
        obj.underlying = other.underlying.copy()
        return obj

    @staticmethod
    @bind_native("java/util/Map", "of(Ljava/lang/Object;Ljava/lang/Object;)Ljava/util/Map;")
    async def mapFromKeyValuePairs(method, stack, key, value):
        obj = await (await method.get_parent_class().create_instance()).init("()V")
        obj.underlying = {key: value}
        return obj

    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentHashMap", "<init>()V")
    @bind_native("java/util/Map", "<init>()V")
    @bind_native("java/util/TreeMap", "<init>()V")
    @bind_native("java/util/HashMap", "<init>()V")
    @bind_native("java/util/Properties", "<init>()V")
    @bind_native("java/lang/ThreadLocal", "<init>()V")
    def init(method, stack, this):
        this.underlying = {}

    @staticmethod
    @bind_native("java/util/Properties", "<init>(MAP)V")
    @bind_native("java/util/Map", "<init>(MAP)V")
    @bind_native("java/util/HashMap", "<init>(MAP)V")
    def init2(method, stack, this, m):
        this.underlying = m.copy()

    @staticmethod
    @bind_native("java/util/EnumMap", "<init>(Ljava/lang/Class;)V")
    def initEnumMap(method, stack, this, key_type):
        this.underlying = {}
        this.key_type = key_type

    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentHashMap", "clear()V")
    def clear(method, stack, this):
        this.underlying.clear()

    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentHashMap", "containsKey(Ljava/lang/Object;)Z")
    @bind_native("java/util/Properties", "containsKey(Ljava/lang/Object;)Z")
    def containsKey(method, stack, this, key):
        return key in this.underlying

    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentHashMap", "get(Ljava/lang/Object;)Ljava/lang/Object;")
    @bind_native("java/util/EnumMap", "get(Ljava/lang/Object;)Ljava/lang/Object;")
    def getByKey(method, stack, this, key):
        return this.underlying.get(key)

    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentHashMap", "putIfAbsent(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;")
    def putIfAbsent(method, stack, this, key, value):
        if key in this.underlying:
            return this.underlying[key]
        this.underlying[key] = value

    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentHashMap", "put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;")
    @bind_native("java/util/HashMap", "put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;")
    @bind_native("java/util/EnumMap", "put(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;")
    @bind_native("java/util/EnumMap", "put(Ljava/lang/Enum;Ljava/lang/Object;)Ljava/lang/Object;")
    def put(method, stack, this, key, value):
        this.underlying[key] = value
        return value

    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentHashMap", "computeIfAbsent(Ljava/lang/Object;Ljava/util/function/Function;)Ljava/lang/Object;")
    @bind_native("java/util/HashMap", "computeIfAbsent(Ljava/lang/Object;Ljava/util/function/Function;)Ljava/lang/Object;")
    def computeIfAbsent(method, stack, this, key, supplier):
        if key in this.underlying:
            return this.underlying[key]
        return this.underlying.setdefault(key, supplier())

    @staticmethod
    @bind_native("java/lang/ThreadLocal", "get()Ljava/lang/Object;")
    async def get(method, stack, this):
        if "value " not in this.underlying:
            this.underlying["value"] = await (await this.get_method("initialValue", "()Ljava/lang/Object;")).invoke([this])
        return this.underlying["value"]

    @staticmethod
    @bind_native("java/util/HashMap", "getOrDefault(Ljava/lang/Object;Ljava/lang/Object;)Ljava/lang/Object;")
    def getOrDefault(method, stack, this, key, default):
        return default if key not in this.underlying else this.underlying[key]

    @staticmethod
    @bind_native("java/lang/ThreadLocal", "set(Ljava/lang/Object;)V")
    def set(method, stack, this, value):
        this.underlying["value"] = value

    @staticmethod
    @bind_native("java/util/HashMap", "forEach(Ljava/util/function/BiConsumer;)V")
    def forEach(method, stack, this, consumer):
        for v in this.underlying.items():
            consumer(*v)

    @staticmethod
    @bind_native("java/util/Map", "entrySet()Ljava/util/Set;")
    async def entrySet(method, stack, this):
        obj = await (await (await stack.vm.get_class("java/util/Set")).create_instance()).init("()V")
        obj.underlying |= set(this.underlying.entries())
        return obj

    @staticmethod
    @bind_native("java/util/Properties", "entrySet()Ljava/util/Set;")
    async def entrySet(method, stack, this):
        return await (await (await stack.vm.get_class("java/util/Set")).create_instance()).init("()V")

    @staticmethod
    @bind_native("java/util/EnumMap", "values()Ljava/util/Collection;")
    async def values(method, stack, this):
        base = await (await (await stack.vm.get_class("java/util/List")).create_instance()).init("()V")
        base.underlying = list(this.underlying.values())
        return base


class QueueLike:
    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentLinkedQueue", "<init>()V")
    @bind_native("java/util/concurrent/LinkedBlockingQueue", "<init>()V")
    def init(method, stack, this):
        this.underlying = collections.deque()


class LockLike:
    @staticmethod
    @bind_native("java/util/concurrent/locks/ReentrantReadWriteLock", "<init>()V")
    @bind_native("java/util/concurrent/locks/ReentrantLock", "<init>()V")
    def init(method, stack, this):
        this.underlying = threading.Lock()

    @staticmethod
    @bind_native("java/util/concurrent/locks/ReentrantLock", "lockInterruptibly()V")
    def lockInterruptibly(method, stack, this):
        this.underlying.acquire()

    @staticmethod
    @bind_native("java/util/concurrent/locks/ReentrantLock", "unlock()V")
    def unlock(method, stack, this):
        this.underlying.release()


class StreamLike:
    @staticmethod
    @bind_native("java/util/stream/Stream", "of([Ljava/lang/Object;)Ljava/util/stream/Stream;")
    async def of(method, stack, array):
        obj = await (await method.get_parent_class().create_instance()).init("()V")
        obj.underlying = array.copy()
        return obj

    @staticmethod
    @bind_native("java/util/stream/Stream", "<init>()V")
    def init(method, stack, this):
        this.underlying = tuple()

    @staticmethod
    @bind_native("java/util/stream/Stream", "<init>(ARRAY)V")
    def init(method, stack, this, array):
        this.underlying = tuple(array)

    @staticmethod
    @bind_native("java/util/stream/Stream", "sorted(Ljava/util/Comparator;)Ljava/util/stream/Stream;")
    async def sortedStream(method, stack, this, comparator):
        # This work-around is so we can use an async function for sorting
        original = list(this.underlying)
        if isinstance(comparator, AbstractMethod):
            sortable = [(e, await comparator.invoke((e,), stack=stack)) for e in original]
        else:
            sortable = [(e, await comparator(e)) for e in original]

        sortable.sort(key=lambda e: e[1])
        this.underlying = [e[0] for e in sortable]
        return this

    @staticmethod
    @bind_native("java/util/stream/Stream", "map(Ljava/util/function/Function;)Ljava/util/stream/Stream;")
    async def mapStream(method, stack, this, function):
        this.underlying = [await function.invoke((e,)) for e in this.underlying]
        return this

    @staticmethod
    @bind_native("java/util/stream/Stream", "concat(Ljava/util/stream/Stream;Ljava/util/stream/Stream;)Ljava/util/stream/Stream;")
    async def concatStreams(method, stack, stream_a, stream_b):
        stream = await (await method.get_parent_class().create_instance()).init("()V")
        stream.underlying = list(stream_a.underlying) + list(stream_b.underlying)
        return stream

    @staticmethod
    @bind_native("java/util/stream/Stream", "toList()Ljava/util/List;")
    async def toList(method, stack, this):
        obj = await (await (await stack.vm.get_class("java/util/List")).create_instance()).init("()V")
        obj.underlying = list(this.underlying)
        return obj

    @staticmethod
    @bind_native("java/util/stream/Collectors", "toList()Ljava/util/stream/Collector;")
    def toList(method, stack):
        return lambda e: list(e.underlying)

    @staticmethod
    @bind_native("java/util/stream/Collectors", "toMap(Ljava/util/function/Function;Ljava/util/function/Function;)Ljava/util/stream/Collector;")
    async def toMapCollector(method, stack, func_a, func_b):
        cls = (await (await stack.vm.get_class("java/util/HashMap")).create_instance())

        async def work(e):
            return await cls.init("(MAP)V", (
                {await func_a.invoke((x,)): await func_b.invoke((x,)) for x in e}
                if not isinstance(e, NativeClassInstance)
                else {await func_a.invoke((x,)): await func_b.invoke((x,)) for x in e.underlying}
            ))

        return work

    @staticmethod
    @bind_native("java/util/stream/Stream", "filter(Ljava/util/function/Predicate;)Ljava/util/stream/Stream;")
    async def filterStream(method, stack, this, predicate):
        if not this.underlying: return this

        first = this.underlying[0]
        first_included = predicate.invoke((first,))
        if isinstance(first_included, typing.Awaitable):
            first_included = await first_included
            this.underlying = ([first] if first_included else []) + [e for e in this.underlying[1:] if await predicate.invoke((e,))]

        else:
            this.underlying = ([first] if first_included else []) + [e for e in this.underlying[1:] if predicate.invoke((e,))]

        return this

    @staticmethod
    @bind_native("java/util/stream/Stream", "collect(Ljava/util/stream/Collector;)Ljava/lang/Object;")
    def collectStream(method, stack, this, collector):
        if callable(collector):
            return collector(this)
        if collector is None:
            return None
        return None  # todo: implement

    @staticmethod
    @bind_native("java/util/stream/Stream", "reduce(Ljava/util/function/BinaryOperator;)Ljava/util/Optional;")
    def reduceStream(method, stack, this, operator):
        value = None
        for e in this.underlying:
            value = operator(value, e)
        return value

    @staticmethod
    @bind_native("java/util/stream/Collectors", "toSet()Ljava/util/stream/Collector;")
    def toSetCollector(method, stack):
        return lambda e: set(e.underlying)

    @staticmethod
    @bind_native("java/util/Comparator", "comparing(Ljava/util/function/Function;)Ljava/util/Comparator;")
    def comparing(method, stack, function):
        async def transform(obj):
            return await function.invoke((obj,))

        return transform

    @staticmethod
    @bind_native("java/util/Comparator", "comparingLong(Ljava/util/function/ToLongFunction;)Ljava/util/Comparator;")
    def comparingLong(method, stack, function):
        def transform(obj):
            return function(obj)
        return transform

    @staticmethod
    @bind_native("java/util/Comparator", "thenComparingInt(Ljava/util/function/ToIntFunction;)Ljava/util/Comparator;")
    def thanComparingInt(method, stack, this, function):
        def transform(obj):
            return this(obj), function(obj)
        return transform

    @staticmethod
    @bind_native("java/util/Comparator", "thenComparing(Ljava/util/function/Function;)Ljava/util/Comparator;")
    def thanComparing(method, stack, this, function):
        def transform(obj):
            return this(obj), function(obj)
        return transform


class RuntimePermission:
    @staticmethod
    @bind_native("java/lang/RuntimePermission", "<init>(Ljava/lang/String;)V")
    def init(method, stack, this, string):
        this.string = string


class SecurityManager:
    @staticmethod
    @bind_native("java/lang/SecurityManager", "checkPermission(Ljava/security/Permission;)V")
    def checkPermission(method, stack, this, permission):
        pass


class AccessController:
    @staticmethod
    @bind_native("java/security/AccessController", "doPrivileged(Ljava/security/PrivilegedAction;)Ljava/lang/Object;")
    def doPrivilegedAction(method, stack, action):
        # todo: invoke
        pass


class System:
    SECURITY_MANAGER = None
    PROPERTIES = {}

    @staticmethod
    @bind_native("java/lang/System", "getSecurityManager()Ljava/lang/SecurityManager;")
    async def getSecurityManager(method, stack: AbstractStack):
        if System.SECURITY_MANAGER is None:
            System.SECURITY_MANAGER = await (await (await stack.vm.get_class("java/lang/SecurityManager")).create_instance()).init("()V")

        return System.SECURITY_MANAGER

    @staticmethod
    @bind_native("java/lang/System", "getProperties()Ljava/util/Properties;")
    async def getProperties(method, stack):
        return await (await (await stack.vm.get_class("java/util/Properties")).create_instance()).init("(MAP)V", System.PROPERTIES)

    @staticmethod
    @bind_native("java/lang/System", "getProperty(Ljava/lang/String;)Ljava/lang/String;")
    @bind_native("java/lang/Object", "getProperty(Ljava/lang/String;)Ljava/lang/String;")
    def getProperty(method, stack, key):
        return System.PROPERTIES.setdefault(key, "")

    @staticmethod
    @bind_native("java/lang/System", "containsProperty(Ljava/lang/String;)Z")
    def containsProperty(method, stack, key):
        return key in System.PROPERTIES

    @staticmethod
    @bind_native("java/lang/Object", "containsProperty(Ljava/lang/String;)Z")
    def containsProperty(method, stack, _, key):
        return key in System.PROPERTIES

    @staticmethod
    @bind_native("java/lang/System", "arraycopy(Ljava/lang/Object;ILjava/lang/Object;II)V")
    def arraycopy(method, stack, source: list, start: int, target: list, new_start: int, size: int):
        target[new_start:new_start + size] = source[start:start + size]

    @staticmethod
    @bind_native("java/lang/System", "currentTimeMillis()")
    def currentTimeMillis(method, stack):
        return round(time.time() * 1000)


class Thread:
    CURRENT = None
    CURRENT_CLASS_LOADER = None

    @staticmethod
    @bind_native("java/lang/Thread", "currentThread()Ljava/lang/Thread;")
    async def currentThread(method: AbstractMethod, stack):
        if Thread.CURRENT is None:
            Thread.CURRENT = await (await method.get_parent_class().create_instance()).init("()V")

        return Thread.CURRENT

    @staticmethod
    @bind_native("java/lang/Thread", "getContextClassLoader()Ljava/lang/ClassLoader;")
    @bind_native("java/lang/Class", "getClassLoader()Ljava/lang/ClassLoader;")
    @bind_native("java/lang/ClassLoader", "getSystemClassLoader()Ljava/lang/ClassLoader;")
    async def getContextClassLoader(method, stack: AbstractStack, *_):
        if Thread.CURRENT_CLASS_LOADER is None:
            Thread.CURRENT_CLASS_LOADER = await (await (await stack.vm.get_class("java/lang/ClassLoader")).create_instance()).init("()V")

        return Thread.CURRENT_CLASS_LOADER


class Method:
    @staticmethod
    @bind_native("java/lang/reflect/Constructor", "newInstance([Ljava/lang/Object;)Ljava/lang/Object;")
    async def newInstance(method, stack, constructor: JavaMethod, args):
        obj = await (await constructor.get_class()).create_instance()
        await constructor.invoke([obj] + list(args))
        return obj


class Class:
    @staticmethod
    @bind_native("java/lang/Class", "getAnnotation(Ljava/lang/Class;)Ljava/lang/annotation/Annotation;")
    def getAnnotation(method, stack, this_cls, annotation_cls):
        return []  # todo: implement

    @staticmethod
    @bind_native("java/lang/Class", "getDeclaredField(Ljava/lang/String;)Ljava/lang/reflect/Field;")
    def getDeclaredField(method, stack, this, name: str):
        return name, this

    @staticmethod
    @bind_native("java/lang/Class", "desiredAssertionStatus()Z")
    def getDesiredAssertionStatus(method, stack, this):
        return False


class ClassField:
    @staticmethod
    @bind_native("java/lang/reflect/Field", "setAccessible(Z)V")
    def setAccessible(method, stack, this, accessible: bool):
        pass  # by default, we give access to fields to all, including for private fields

    @staticmethod
    @bind_native("java/lang/reflect/Field", "get(Ljava/lang/Object;)Ljava/lang/Object;")
    async def getValue(method, stack, this, obj):
        try:
            return obj.get_field(this[0])
        except (KeyError, AttributeError):
            if hasattr(obj, this[0]):
                return getattr(obj, this[0])

            try:
                return await this[1].get_static_attribute(this[0])
            except (AttributeError, KeyError):
                raise StackCollectingException(f"{obj} has no attribute '{this[0]}'") from None


class ClassLoader:
    @staticmethod
    @bind_native("java/lang/ClassLoader", "getResources(Ljava/lang/String;)Ljava/util/Enumeration;")
    async def getResources(method, stack, this, resource):
        return await (await (await stack.vm.get_class("java/util/Enumeration")).create_instance()).init("()V")

    @staticmethod
    @bind_native("java/lang/Class", "forName(Ljava/lang/String;)Ljava/lang/Class;")
    async def forName(method, stack, name):
        return await stack.vm.get_class(name)

    @staticmethod
    @bind_native("java/lang/Class", "getName()Ljava/lang/String;")
    def getName(method, stack, this: jvm.api.AbstractJavaClass):
        return this.name

    @staticmethod
    @bind_native("java/lang/Class", "newInstance()Ljava/lang/Object;")
    async def newInstance(method, stack, this: jvm.api.AbstractJavaClass):
        return await this.create_instance()


class ServiceLoader:
    @staticmethod
    @bind_native("java/util/ServiceLoader", "load(Ljava/lang/Class;Ljava/lang/ClassLoader;)Ljava/util/ServiceLoader;")
    async def load(method, stack, cls, class_loader):
        return await method.get_parent_class().create_instance()

    @staticmethod
    @bind_native("java/util/ServiceLoader", "iterator()Ljava/util/Iterator;")
    async def iterator(method, stack, this):
        return await (await (await stack.vm.get_class("java/util/Iterator")).create_instance()).init("(ITERABLE)V", [])


class Enumeration:
    @staticmethod
    @bind_native("java/util/Enumeration", "hasMoreElements()Z")
    def hasMoreElements(method, stack, this):
        return len(this.underlying) > 0

    @staticmethod
    @bind_native("java/util/Enumeration", "nextElement()Ljava/lang/Object;")
    def nextElement(method, stack, this):
        return this.underlying.pop(0)


class String:
    @staticmethod
    @bind_native("java/lang/String", "split(Ljava/lang/String;)[Ljava/lang/String;")
    def split(method, stack, string, at):
        return string.split(at)

    @staticmethod
    @bind_native("java/lang/String", "toLowerCase()Ljava/lang/String;")
    def toLowerCase(method, stack, this: str):
        return this.lower()

    @staticmethod
    @bind_native("java/lang/CharSequence", "length()I")
    def length(method, stack, this):
        return len(this)

    @staticmethod
    @bind_native("java/lang/StringBuilder", "<init>()V")
    def init(method, stack, this):
        this.underlying = []

    @staticmethod
    @bind_native("java/lang/StringBuilder", "append(Ljava/lang/String;)Ljava/lang/StringBuilder;")
    def append(method, stack, this, data):
        this.underlying.append(str(data))
        return this

    @staticmethod
    @bind_native("java/lang/StringBuilder", "toString()Ljava/lang/String;")
    def toString(method, stack, this):
        return "".join(this.underlying)

    @staticmethod
    @bind_native("java/lang/String", "lastIndexOf(Ljava/lang/String;)I")
    def lastIndexOf(method, stack, this: str, search: str):
        return this.rindex(search) if search in this else -1

    @staticmethod
    @bind_native("java/lang/String", "contains(Ljava/lang/CharSequence;)Z")
    def containsSubSequence(method, stack, this: str, compare: str):
        return compare in this

    @staticmethod
    @bind_native("java/lang/String", "replaceAll(Ljava/lang/String;Ljava/lang/String;)Ljava/lang/String;")
    def replaceAll(method, stack, this: str, before: str, after: str):
        return this.replace(before, after)

    @staticmethod
    @bind_native("java/lang/String", "replace(Ljava/lang/CharSequence;Ljava/lang/CharSequence;)Ljava/lang/String;")
    def replaceAll(method, stack, this: str, before: str, after: str):
        return this.replace(before, after, 1)

    @staticmethod
    @bind_native("java/lang/String", "equalsIgnoreCase(Ljava/lang/String;)Z")
    def equalsIgnoreCase(method, stack, this: str, other: str):
        return this.lower() == other.lower()

    @staticmethod
    @bind_native("java/lang/String", "endsWith(Ljava/lang/String;)Z")
    def endsWith(method, stack, this: str, other: str):
        return this.endswith(other)

    @staticmethod
    @bind_native("java/lang/String", "getBytes()[B")
    def getBytes(method, stack, this: str):
        return this.encode("utf-8")  # todo: is this correct?

    @staticmethod
    @bind_native("java/lang/String", "trim()Ljava/lang/String;")
    def trimString(method, stack, this):
        return this.trim()

    @staticmethod
    @bind_native("java/lang/String", "toLowerCase(Ljava/util/Locale;)Ljava/lang/String;")
    def toLowerCase(method, stack, this, locale):
        return this.lower()

    @staticmethod
    @bind_native("java/lang/String", "isEmpty()Z")
    def isEmpty(method, stack, this):
        return len(this) == 0


class Math:
    @staticmethod
    @bind_native("java/lang/Math", "max(II)I")
    @bind_native("java/lang/Math", "max(JJ)J")
    @bind_native("java/lang/Math", "max(FF)F")
    @bind_native("java/lang/Math", "max(DD)D")
    def getMax(method, stack, a, b):
        return max(a, b)

    @staticmethod
    @bind_native("java/lang/Math", "min(II)I")
    @bind_native("java/lang/Math", "min(JJ)J")
    @bind_native("java/lang/Math", "min(FF)F")
    @bind_native("java/lang/Math", "min(DD)D")
    def getMin(method, stack, a, b):
        return min(a, b)


class Regex:
    @staticmethod
    @bind_native("java/util/regex/Pattern", "compile(Ljava/lang/String;)Ljava/util/regex/Pattern;")
    async def compile(method, stack, pattern):
        return await (await method.get_parent_class().create_instance()).init("(PATTERN)V", re.compile(pattern))


class Pattern:
    @staticmethod
    @bind_native("java/util/regex/Pattern", "<init>(PATTERN)V")
    def init(method, stack, this, pattern: re.Pattern):
        this.underlying = pattern

    @staticmethod
    @bind_native("java/util/regex/Pattern", "matcher(Ljava/lang/CharSequence;)Ljava/util/regex/Matcher;")
    async def matcher(method, stack, this, sequence: str):
        regex: re.Pattern = this.underlying
        return await (await (await stack.vm.get_class("java/util/regex/Matcher")).create_instance()).init("(MATCH)V", regex.match(sequence))


class Matcher:
    @staticmethod
    @bind_native("java/util/regex/Matcher", "<init>(MATCH)V")
    def init(method, stack, this, matcher: re.Match):
        this.underlying = matcher
        this.matched = False

    @staticmethod
    @bind_native("java/util/regex/Matcher", "find()Z")
    def find(method, stack, this):
        match: re.Match = this.underlying
        return len(match.groups()) > 0 and not this.matched

    @staticmethod
    @bind_native("java/util/regex/Matcher", "group(I)Ljava/lang/String;")
    def group(method, stack, this, index) -> str:
        match = this.underlying.group(index)
        this.matched = True
        return match


class Enum:
    @staticmethod
    @bind_native("java/lang/Enum", "<init>(Ljava/lang/String;I)V")
    def init(method, stack, this, name, index):
        this.name = name
        this.index = index

    @staticmethod
    @bind_native("java/lang/Enum", "toString()Ljava/lang/String;")
    def toString(method, stack, this) -> str:
        return str(this)

    @staticmethod
    @bind_native("java/lang/Enum", "name()Ljava/lang/String;")
    def nameOfValue(method, stack, this):
        return this.split("::")[-1] if isinstance(this, str) else this.name


class JException:
    @staticmethod
    @bind_native("java/lang/IllegalStateException", "<init>(Ljava/lang/String;)V")
    def init(method, stack, this, message):
        this.fields["message"] = message


class MethodImpl:
    @staticmethod
    @bind_native("java/lang/reflect/Method", "apply(Ljava/lang/Object;)Ljava/lang/Object;")
    async def apply(method, stack, this, *args):
        return await this.invoke(args)


class Asserts:
    @staticmethod
    @bind_native("java/util/Objects", "requireNonNull(Ljava/lang/Object;)Ljava/lang/Object;")
    def requireNonNull(method, stack, obj):
        if obj is None:
            raise StackCollectingException("Object is null")
        return obj


class IO:
    @staticmethod
    @bind_native("java/nio/file/Path", "toAbsolutePath()Ljava/nio/file/Path;")
    @bind_native("java/nio/file/Path", "toString()Ljava/lang/String;")
    def toAbsolutePath(method, stack, this):
        return this

    @staticmethod
    @bind_native("java/nio/file/Paths", "get(Ljava/lang/String;[Ljava/lang/String;)Ljava/nio/file/Path;")
    def joinPathTree(method, stack, root, parts):
        return os.path.join(root, *parts)

    @staticmethod
    @bind_native("java/nio/file/Files", "createDirectory(Ljava/nio/file/Path;[Ljava/nio/file/attribute/FileAttribute;)Ljava/nio/file/Path;")
    def makeDirs(method, stack, path, config):
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    @bind_native("java/io/File", "<init>(Ljava/lang/String;)V")
    def init(method, stack, this, path: str):
        this.underlying = path

    @staticmethod
    @bind_native("java/io/File", "<init>(Ljava/io/File;Ljava/lang/String;)V")
    def initFromFile(method, stack, this, file, end: str):
        this.underlying = os.path.join(file.underlying, end)

    @staticmethod
    @bind_native("java/io/File", "mkdirs/(Z")
    def mkdirs(method, stack, this):
        os.makedirs(this.underlying, exist_ok=True)
        return True

    @staticmethod
    @bind_native("java/nio/file/Path", "toFile()Ljava/io/File;")
    def toFile(method, stack, this):
        return this

    @staticmethod
    @bind_native("java/io/PrintStream", "println(Ljava/lang/String;)V")
    def println(method, stack, this, text: str):
        print("[JAVA] "+text)


class StringConcatFactory:
    @staticmethod
    @bind_native("java/lang/invoke/StringConcatFactory", "makeConcatWithConstants(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;")
    def makeConcatWithConstants(method, stack, lookup, *args):
        text = ""
        for arg in args[1][1][0][1][1]:
            if arg == "\x01":
                text += stack.pop()
            elif arg == "\x02":
                raise NotImplementedError
            else:
                text += arg
        return text


class Repeatable:
    @staticmethod
    @bind_annotation("java/lang/annotation/Repeatable")
    def noAnnotationProcessing(method, stack, target, args):
        pass


class Random:
    @staticmethod
    @bind_native("java/util/Random", "<init>()V")
    def init(method, stack, this):
        pass


class Supplier:
    @staticmethod
    @bind_native("java/util/function/Supplier", "get()Ljava/lang/Object;")
    def getValue(method, stack, this):
        return this()


class Record:
    @staticmethod
    @bind_native("java/lang/Record", "<init>()V")
    def init(method, stack, this):
        pass


class UUID:
    @staticmethod
    @bind_native("java/util/UUID", "fromString(Ljava/lang/String;)Ljava/util/UUID;")
    async def uuidFromString(method, stack, string: str):
        obj = await method.get_parent_class().create_instance()
        obj.underlying = uuid.UUID(string)
        return obj

    @staticmethod
    @bind_native("java/util/UUID", "nameUUIDFromBytes([B)Ljava/util/UUID;")
    async def nameUUIDFromBytes(method, stack, array):
        obj = await method.get_parent_class().create_instance()
        obj.underlying = uuid.UUID(bytes=bytes(array))
        return obj


class Optional:
    @staticmethod
    @bind_native("java/util/Optional", "get()Ljava/lang/Object;")
    def getOptionalValue(method, stack, this):
        if this is None:
            raise StackCollectingException("<this> is None")
        return this


class Object:
    @staticmethod
    @bind_native("java/lang/Object", "getClass()Ljava/lang/Class;")
    async def getClass(method, stack, this):
        return None if this is None or not hasattr(this, "get_class") else await this.get_class()


class Atomics:
    @staticmethod
    @bind_native("java/util/concurrent/atomic/AtomicInteger", "<init>(I)V")
    def init(method, stack, this, value):
        this.underlying = value
        this.lock = threading.Lock()

    @staticmethod
    @bind_native("java/util/concurrent/atomic/AtomicInteger", "getAndIncrement()I")
    def getAndIncrement(method, stack, this):
        this.lock.acquire()
        v = this.underlying
        this.underlying += 1
        this.lock.release()
        return v

