import collections
import os.path
import re
import threading
import time
import uuid

import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.JavaExceptionStack import StackCollectingException
from jvm.natives import bind_native, bind_annotation
from mcpython.engine import logger


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
    @bind_native("java/util/Properties", "entrySet()Ljava/util/Set;")
    def entrySet(method, stack, this):
        return stack.vm.get_class("java/util/Set").create_instance().init("()V")

    @staticmethod
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
    @bind_native("java/util/LinkedHashSet", "add(Ljava/lang/Object;)Z")
    @bind_native("java/util/TreeSet", "add(Ljava/lang/Object;)Z")
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
    @bind_native("java/util/LinkedHashSet", "size()I")
    def getSize(method, stack, this):
        return len(this.underlying)

    @staticmethod
    @bind_native("java/util/LinkedHashSet", "iterator()Ljava/util/Iterator;")
    @bind_native("java/util/Set", "iterator()Ljava/util/Iterator;")
    @bind_native("java/util/TreeSet", "iterator()Ljava/util/Iterator;")
    @bind_native("java/util/EnumSet", "iterator()Ljava/util/Iterator;")
    def iterator(method, stack, this):
        return stack.vm.get_class("java/util/Iterator").create_instance().init("(ITERABLE)V", list(this.underlying))

    @staticmethod
    @bind_native("java/util/LinkedHashSet", "toArray([Ljava/lang/Object;)[Ljava/lang/Object;")
    def toArray(method, stack, this, array: list):
        array.clear()
        array.extend(this.underlying)
        return array

    @staticmethod
    @bind_native("java/util/EnumSet", "allOf(Ljava/lang/Class;)Ljava/util/EnumSet;")
    def allOf(method, stack, cls: jvm.api.AbstractJavaClass):
        return stack.vm.get_class("java/util/EnumSet").create_instance().init("(SOURCE)V", cls.get_enum_values())

    @staticmethod
    @bind_native("java/util/HashSet", "isEmpty()Z")
    def isEmpty(method, stack, this):
        return len(this.underlying) == 0


class ListLike:
    @staticmethod
    @bind_native("java/util/Enumeration", "<init>()V")
    @bind_native("java/util/ArrayList", "<init>()V")
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
    def singletonList(method, stack, obj):
        return stack.vm.get_class("java/util/Iterator").create_instance().init("(ITERABLE)V", [obj])

    @staticmethod
    @bind_native("java/util/Iterator", "hasNext()Z")
    def hasNext(method, stack, this):
        return len(this.underlying) > 0

    @staticmethod
    @bind_native("java/util/Iterator", "next()Ljava/lang/Object;")
    def nextElement(method, stack, this):
        return this.underlying.pop(0)

    @staticmethod
    @bind_native("java/util/ArrayList", "add(Ljava/lang/Object;)Z")
    @bind_native("java/util/concurrent/CopyOnWriteArrayList", "add(Ljava/lang/Object;)Z")
    def add(method, stack, this, obj):
        this.underlying.append(obj)
        return True

    @staticmethod
    @bind_native("java/util/concurrent/CopyOnWriteArrayList", "size()I")
    @bind_native("java/util/ArrayList", "size()I")
    def size(method, stack, this):
        return len(this.underlying)

    @staticmethod
    @bind_native("java/util/Arrays", "asList([Ljava/lang/Object;)Ljava/util/List;")
    def asList(method, stack, this):
        return list(this)

    @staticmethod
    @bind_native("java/util/ArrayList", "clear()V")
    def clearArrayList(method, stack, this):
        this.underlying.clear()


class MapLike:
    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentHashMap", "<init>()V")
    @bind_native("java/util/TreeMap", "<init>()V")
    @bind_native("java/util/HashMap", "<init>()V")
    @bind_native("java/util/Properties", "<init>()V")
    @bind_native("java/lang/ThreadLocal", "<init>()V")
    def init(method, stack, this):
        this.underlying = {}

    @staticmethod
    @bind_native("java/util/Properties", "<init>(MAP)V")
    def init2(method, stack, this, m):
        this.underlying = m.copy()

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
    def put(method, stack, this, key, value):
        this.underlying[key] = value
        return value

    @staticmethod
    @bind_native("java/lang/ThreadLocal", "get()Ljava/lang/Object;")
    def get(method, stack, this):
        if "value " not in this.underlying:
            this.underlying["value"] = this.get_method("initialValue", "()Ljava/lang/Object;").invoke([this])
        return this.underlying["value"]

    @staticmethod
    @bind_native("java/lang/ThreadLocal", "set(Ljava/lang/Object;)V")
    def set(method, stack, this, value):
        this.underlying["value"] = value


class QueueLike:
    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentLinkedQueue", "<init>()V")
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
    def getSecurityManager(method, stack: AbstractStack):
        if System.SECURITY_MANAGER is None:
            System.SECURITY_MANAGER = stack.vm.get_class("java/lang/SecurityManager").create_instance().init("()V")

        return System.SECURITY_MANAGER

    @staticmethod
    @bind_native("java/lang/System", "getProperties()Ljava/util/Properties;")
    def getProperties(method, stack):
        return stack.vm.get_class("java/util/Properties").create_instance().init("(MAP)V", System.PROPERTIES)

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
    def currentThread(method: AbstractMethod, stack):
        if Thread.CURRENT is None:
            Thread.CURRENT = method.get_class().create_instance().init("()V")

        return Thread.CURRENT

    @staticmethod
    @bind_native("java/lang/Thread", "getContextClassLoader()Ljava/lang/ClassLoader;")
    @bind_native("java/lang/Class", "getClassLoader()Ljava/lang/ClassLoader;")
    @bind_native("java/lang/ClassLoader", "getSystemClassLoader()Ljava/lang/ClassLoader;")
    def getContextClassLoader(method, stack: AbstractStack, *_):
        if Thread.CURRENT_CLASS_LOADER is None:
            Thread.CURRENT_CLASS_LOADER = stack.vm.get_class("java/lang/ClassLoader").create_instance().init("()V")

        return Thread.CURRENT_CLASS_LOADER


class ClassLoader:
    @staticmethod
    @bind_native("java/lang/ClassLoader", "getResources(Ljava/lang/String;)Ljava/util/Enumeration;")
    def getResources(method, stack, this, resource):
        return stack.vm.get_class("java/util/Enumeration").create_instance().init("()V")

    @staticmethod
    @bind_native("java/lang/Class", "forName(Ljava/lang/String;)Ljava/lang/Class;")
    def forName(method, stack, name):
        return stack.vm.get_class(name)

    @staticmethod
    @bind_native("java/lang/Class", "getName()Ljava/lang/String;")
    def getName(method, stack, this: jvm.api.AbstractJavaClass):
        return this.name

    @staticmethod
    @bind_native("java/lang/Class", "newInstance()Ljava/lang/Object;")
    def newInstance(method, stack, this: jvm.api.AbstractJavaClass):
        return this.create_instance()


class ServiceLoader:
    @staticmethod
    @bind_native("java/util/ServiceLoader", "load(Ljava/lang/Class;Ljava/lang/ClassLoader;)Ljava/util/ServiceLoader;")
    def load(method, stack, cls, class_loader):
        return method.get_class().create_instance()

    @staticmethod
    @bind_native("java/util/ServiceLoader", "iterator()Ljava/util/Iterator;")
    def iterator(method, stack, this):
        return stack.vm.get_class("java/util/Iterator").create_instance().init("(ITERABLE)V", [])


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
    @bind_native("java/lang/String", "equalsIgnoreCase(Ljava/lang/String;)Z")
    def equalsIgnoreCase(method, stack, this: str, other: str):
        return this.lower() == other.lower()

    @staticmethod
    @bind_native("java/lang/String", "endsWith(Ljava/lang/String;)Z")
    def endsWith(method, stack, this: str, other: str):
        return this.endswith(other)


class Regex:
    @staticmethod
    @bind_native("java/util/regex/Pattern", "compile(Ljava/lang/String;)Ljava/util/regex/Pattern;")
    def compile(method, stack, pattern):
        return method.get_class().create_instance().init("(PATTERN)V", re.compile(pattern))


class Pattern:
    @staticmethod
    @bind_native("java/util/regex/Pattern", "<init>(PATTERN)V")
    def init(method, stack, this, pattern: re.Pattern):
        this.underlying = pattern

    @staticmethod
    @bind_native("java/util/regex/Pattern", "matcher(Ljava/lang/CharSequence;)Ljava/util/regex/Matcher;")
    def matcher(method, stack, this, sequence: str):
        regex: re.Pattern = this.underlying
        return stack.vm.get_class("java/util/regex/Matcher").create_instance().init("(MATCH)V", regex.match(sequence))


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


class JException:
    @staticmethod
    @bind_native("java/lang/IllegalStateException", "<init>(Ljava/lang/String;)V")
    def init(method, stack, this, message):
        this.fields["message"] = message


class Method:
    @staticmethod
    @bind_native("java/lang/reflect/Method", "apply(Ljava/lang/Object;)Ljava/lang/Object;")
    def apply(method, stack, this, *args):
        return this.invoke(args)


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
        logger.println("[JAVA] "+text)


class StringConcatFactory:
    @staticmethod
    @bind_native("java/lang/invoke/StringConcatFactory", "makeConcatWithConstants(Ljava/lang/invoke/MethodHandles$Lookup;Ljava/lang/String;Ljava/lang/invoke/MethodType;Ljava/lang/String;[Ljava/lang/Object;)Ljava/lang/invoke/CallSite;")
    def makeConcatWithConstants(method, stack, lookup, *args):
        print(args)


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
    def uuidFromString(method, stack, string: str):
        obj = method.get_class().create_instance()
        obj.underlying = uuid.UUID(string)
        return obj

