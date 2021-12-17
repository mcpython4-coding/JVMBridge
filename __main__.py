import sys
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

cls = vm.get_class(sys.argv[2])
cls.get_method("main", "([Ljava/lang/String;)V")(*sys.argv[3:])

