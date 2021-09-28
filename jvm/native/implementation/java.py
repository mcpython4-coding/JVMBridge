import re

from jvm.api import AbstractMethod
from jvm.api import AbstractStack
from jvm.natives import bind_native


@bind_native("java/lang/Object", "<init>()V")
@bind_native("java/util/Properties", "<init>()V")
@bind_native("java/lang/SecurityManager", "<init>()V")
@bind_native("java/lang/ClassLoader", "<init>()V")
@bind_native("java/lang/ThreadLocal", "<init>()V")
@bind_native("java/lang/ClassLoader", "getParent()Ljava/lang/ClassLoader;")
def noAction(method, stack, this):
    pass


@bind_native("java/lang/Boolean", "valueOf(Z)Ljava/lang/Boolean;")
@bind_native("java/lang/Boolean", "booleanValue()Z")
def thisMap(method, stack, this):
    return this


class SetLike:
    @staticmethod
    @bind_native("java/util/Properties", "entrySet()Ljava/util/Set;")
    def entrySet(method, stack, this):
        return stack.vm.get_class("java/util/Set").create_instance().init("()V")

    @staticmethod
    @bind_native("java/util/LinkedHashSet", "<init>()V")
    @bind_native("java/util/Set", "<init>()V")
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
    def iterator(method, stack, this):
        return stack.vm.get_class("java/util/Iterator").create_instance().init("(ITERABLE)V", list(this.underlying))

    @staticmethod
    @bind_native("java/util/LinkedHashSet", "toArray([Ljava/lang/Object;)[Ljava/lang/Object;")
    def toArray(method, stack, this, array: list):
        array.clear()
        array.extend(this.underlying)
        return array


class ListLike:
    @staticmethod
    @bind_native("java/util/Enumeration", "<init>()V")
    @bind_native("java/util/ArrayList", "<init>()V")
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


class MapLike:
    @staticmethod
    @bind_native("java/util/concurrent/ConcurrentHashMap", "<init>()V")
    @bind_native("java/util/Properties", "<init>()V")
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
        return this.underlying.setdefault(key, value)


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
    def matcher(method, stack, this, sequence):
        pass




