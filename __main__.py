import sys
import jvm.Java
import jvm.JavaVM
import jvm.Runtime
import zipfile
import os


jvm.Java.vm.init_builtins()
if "--init-bridge" in sys.argv:
    jvm.Java.vm.init_bridge()
    sys.argv.remove("--init-bridge")


file = sys.argv[1]


if zipfile.is_zipfile(file):
    f = zipfile.ZipFile(file)
    jvm.JavaVM.get_bytecode_of_class = lambda cls: f.read(cls + ".class")
elif os.path.isdir(file):
    jvm.JavaVM.get_bytecode_of_class = lambda cls: open(file + "/" + cls + ".class", mode="rb").read()
else:
    raise RuntimeError(f"{file} is no valid input file")

cls = jvm.Java.vm.get_class(sys.argv[2])
cls.get_method("main", "([Ljava/lang/String;)V")(*sys.argv[3:])

