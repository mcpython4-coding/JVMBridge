import os

import asyncio

from jvm.ClassAdressing import DirectoryFileSource
from jvm.JavaExceptionStack import StackCollectingException
from jvm.JavaVM import JavaVM

vm = JavaVM()

local = os.path.dirname(__file__)
vm.add_accessor(DirectoryFileSource(local))

import jvm.natives as natives
natives.manager.vm = vm
natives.manager.load_files()


try:
    cls = asyncio.get_event_loop().run_until_complete(vm.get_class("TestClass"))
    asyncio.get_event_loop().run_until_complete(cls.prepare_use())
    method = asyncio.get_event_loop().run_until_complete(cls.get_method("main", "([Ljava/lang/String;)V"))
    asyncio.get_event_loop().run_until_complete(method.invoke([]))
except StackCollectingException as e:
    print("[FATAL] Error occurred!")
    print(e.format_exception())
    raise

