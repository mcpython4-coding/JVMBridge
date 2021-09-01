import typing

import simplejson
import os

local = os.path.dirname(__file__)


def className2File(name: str, version) -> typing.Optional[str]:
    version = version.replace(".", "_") if isinstance(version, str) else None

    if name.startswith('java/') or name.startswith('javax/'):
        return local+"/binding/java_index.json"

    elif name.startswith("org/apache/logging"):
        return local+"/binding/logger_index.json"

    elif name.startswith("com/google/gson/"):
        return local+"/binding/gson_index.json"

    elif name.startswith("com/google/"):
        return local+"/binding/google_util_index.json"

    elif name.startswith("it/unimi/dsi/fastutil"):
        return local+"/binding/fastutil_index.json"

    elif name.startswith("org/apache/commons/"):
        return local + "/binding/apache_util.json"

    elif name.startswith("io/netty/"):
        return local + "/binding/netty_index.json"

    if version is None: return

    if name.startswith("net/minecraft/") or name.startswith("com/mojang/"):
        return local+f"/binding/mc_{version}_internal_index.json"

    elif name.startswith("net/minecraftforge/"):
        return local + f"/binding/mc_{version}_forge_index.json"

    elif name.startswith("org/spongepowered/asm/mixin/"):
        return local + f"/binding/mc_{version}_mixin_index.json"


def dumpClassCreationToFiles(name: str, version):
    file = className2File(name, version)

    if file is None: return

    with open(file) as f:
        data = simplejson.load(f)

    data.setdefault("classes", {})[name] = {}

    with open(file, mode="w") as f:
        simplejson.dump(data, f, indent="  ", sort_keys=True)


def addClassAttribute(cls_name: str, version, attr_name: str, static=False):
    file = className2File(cls_name, version)

    if file is None: return

    with open(file) as f:
        data = simplejson.load(f)

    config = {}

    if static:
        config["access"] = "static"

    data.setdefault("classes", {}).setdefault(cls_name, {}).setdefault("attributes", {})[attr_name] = config

    with open(file, mode="w") as f:
        simplejson.dump(data, f, indent="  ", sort_keys=True)


def addMethod(cls_name: str, version, signature: str):
    file = className2File(cls_name, version)

    if file is None: return

    with open(file) as f:
        data = simplejson.load(f)

    data.setdefault("classes", {}).setdefault(cls_name, {}).setdefault("methods", {})[signature] = {}

    with open(file, mode="w") as f:
        simplejson.dump(data, f, indent="  ", sort_keys=True)

