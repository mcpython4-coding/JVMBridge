import asyncio
import sys

import asyncio as asyncio

import jvm.JavaVM
import zipfile
import os
import jvm.api
import jvm.ClassAdressing


jvm.api.vm.init_builtins()
if "--init-bridge" in sys.argv:
    import jvm.natives
    jvm.natives.manager.load_files()

    sys.argv.remove("--init-bridge")


# Source file
file = sys.argv[1]
accessor = jvm.ClassAdressing.decide_simple(file)

vm = jvm.JavaVM.JavaVM()
vm.add_accessor(accessor)

cls = asyncio.get_event_loop().run_until_complete(vm.get_class(sys.argv[2]))
asyncio.get_event_loop().run_until_complete(asyncio.get_event_loop().run_until_complete(cls.get_method("main", "([Ljava/lang/String;)V")).invoke(*sys.argv[3:]))

