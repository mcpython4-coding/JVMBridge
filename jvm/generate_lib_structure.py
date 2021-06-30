import os
import sys
import json

try:
    import jvm.Java as Java
except ImportError:
    import Java

Java.vm.simulation = True

import zipfile


# A base string for class generation
CLASS_BASE_STRING = """# JavaFML native implementation of native {native_name}
from jvm.native_base import native, MappedNative


class {friendly_native_name}(MappedNative):
    ""\"
    Implementation of class {native_name}
    ""\"
    NAME = "{native_name}"
    
    IS_ABSTRACT = {is_abstract}
    IS_INTERFACE = {is_interface}
    
    DYNAMIC_FIELD_KEYS = {dynamic_fields}
    STATIC_FIELD_KEYS = {static_fields}
    
{class_body}
"""

# The method base string
METHOD_BASE_STRING = """    @native("{name}", "{signature}"{config})
    def {friendly_name}(self, {args}):
        print(f"invoking not implemented native method {name}{signature} on class {{self.name}}")"""


# Usage generate_lib_structure.py <output folder> <mapping file> [...<source .jar files>]
local = os.path.dirname(__file__)

output_folder = sys.argv[1].replace("./", local+"/")
mapping_file = sys.argv[2].replace("./", local+"/")
jar_files = [e.replace("./", local+"/") for e in sys.argv[3:]]


with open(mapping_file) as f:
    data = f.read()


for file in jar_files:
    with zipfile.ZipFile(file) as f:
        for inner_file in f.namelist():
            # non-class files and package-info classes should be skipped
            if not inner_file.endswith(".class") or "package-info" in inner_file or "module-info" in inner_file: continue
            if "META-INF" in inner_file: continue

            print(f"processing {inner_file}")
            bytecode = f.read(inner_file)

            cls = Java.vm.load_class_from_bytecode(inner_file.removesuffix(".class"), bytecode, prepare=False)

            static_field_names = set()
            dynamic_field_names = set()
            methods = []

            for field_name, field_info in cls.fields.items():
                if field_info.access & 0x0008:
                    static_field_names.add(field_name)
                else:
                    dynamic_field_names.add(field_name)

            names = set()
            for (method_name, method_signature), method_info in cls.methods.items():
                # we don't need the class init
                if method_name == "<clinit>": continue

                # remove lambda methods; they should not be needed in general use
                if method_name.startswith("lambda$"): continue

                friendly_name = method_name.replace("$", "__").replace("<", "").replace(">", "") + "_0"
                while friendly_name in names:
                    friendly_name = "_".join(friendly_name.split("_")[:-1]) + "_" + str(int(friendly_name.split("_")[-1])+1)
                names.add(friendly_name)

                config = ""

                if method_info.access & 0x0008:
                    config += ", static=True"

                if method_info.access & 0x0002:
                    config += ", private=True"

                string = METHOD_BASE_STRING.format(
                    name=method_name,
                    signature=method_signature,
                    friendly_name=friendly_name,
                    config=config,
                    args="*_" if method_info.access & 0x0008 else "instance, *_",
                )

                methods.append(string)

            if methods:
                inner = "\n\n".join(methods)
            else:
                inner = ""

            cls_body = CLASS_BASE_STRING.format(
                class_body=inner,
                native_name=cls.name,
                friendly_native_name=cls.name.split("/")[-1].replace("$", "__"),
                is_abstract=bool(cls.access & 0x0400),
                is_interface=bool(cls.access & 0x0200),
                dynamic_fields=dynamic_field_names,
                static_fields=static_field_names,
            )

            write = os.path.join(output_folder, inner_file.replace(".class", ".py").replace("$", "__"))
            os.makedirs(os.path.dirname(write), exist_ok=True)
            with open(write, mode="w") as fw:
                fw.write(cls_body)

