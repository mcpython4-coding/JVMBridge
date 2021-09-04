import sys
import jvm.JavaVM
import zipfile
import os
import jvm.api


jvm.api.vm.init_builtins()
if "--init-bridge" in sys.argv:
    import jvm.builtinwrapper
    jvm.builtinwrapper.load_default_indexes()

    sys.argv.remove("--init-bridge")


file = sys.argv[1]


if zipfile.is_zipfile(file):
    f = zipfile.ZipFile(file)
    jvm.JavaVM.get_bytecode_of_class = lambda cls: f.read(cls + ".class")
elif os.path.isdir(file):
    jvm.JavaVM.get_bytecode_of_class = lambda cls: open(file + "/" + cls + ".class", mode="rb").read()
else:
    raise RuntimeError(f"{file} is no valid input file as .class source! Allowed are directories and zip-like files (JAR archives)")

cls = jvm.api.vm.get_class(sys.argv[2])
cls.get_method("main", "([Ljava/lang/String;)V")(*sys.argv[3:])

