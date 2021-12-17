import os

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
    cls = vm.get_class("TestClass")
    cls.prepare_use()
    method = cls.get_method("main", "([Ljava/lang/String;)V")
    method.invoke([])
except StackCollectingException as e:
    print("[FATAL] Error occurred!")
    print(e.format_exception())
    raise

