import collections
import re
import threading

import jvm.api
from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.natives import bind_native, bind_annotation


@bind_annotation("javax/annotation/Nullable")
@bind_annotation("javax/annotation/Nonnull")
@bind_annotation("java/lang/annotation/Target")
@bind_annotation("java/lang/annotation/Retention")
@bind_annotation("java/lang/Deprecated")
@bind_annotation("java/lang/FunctionalInterface")
@bind_annotation("java/lang/SafeVarargs")
@bind_annotation("javax/annotation/ParametersAreNonnullByDefault")
@bind_annotation("javax/annotation/meta/TypeQualifierDefault")
def noAnnotation(method, stack, target, args):
    pass


@bind_native("java/lang/Object", "<init>()V")
@bind_native("java/util/Properties", "<init>()V")
@bind_native("java/lang/SecurityManager", "<init>()V")
@bind_native("java/lang/ClassLoader", "<init>()V")
@bind_native("java/lang/ThreadLocal", "initialValue()Ljava/lang/Object;")
@bind_native("java/lang/ClassLoader", "getParent()Ljava/lang/ClassLoader;")
def noAction(method, stack, this):
    pass


@bind_native("java/lang/Boolean", "valueOf(Z)Ljava/lang/Boolean;")
@bind_native("java/lang/Integer", "valueOf(I)Ljava/lang/Integer;")
@bind_native("java/lang/Boolean", "booleanValue()Z")
@bind_native("java/lang/Class", "asSubclass(Ljava/lang/Class;)Ljava/lang/Class;")
def thisMap(method, stack, this, *_):
    return this


@bind_native("java/lang/Integer", "parseInt(Ljava/lang/String;)I")
def parseToInt(method, stack, value):
    try:
        return int(value)
    except ValueError:
        return 0


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
    def initFromIter(method, stack, this, source: list):
        this.underlying = source

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
    def add(method, stack, this, obj):
        this.underlying.append(obj)
        return True

    @staticmethod
    @bind_native("java/util/concurrent/CopyOnWriteArrayList", "size()I")
    def size(method, stack, this):
        return len(this.underlying)


class MapLike:
    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentHashMap", "<init>()V")
    @bind_native("java/util/TreeMap", "<init>()V")
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

