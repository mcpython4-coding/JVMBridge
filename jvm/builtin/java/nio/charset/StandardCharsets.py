from mcpython import shared
from jvm.Java import NativeClass, native


class StandardCharsets(NativeClass):
    NAME = "java/nio/charset/StandardCharsets"

    def __init__(self):
        super().__init__()
        self.exposed_attributes.update({
            "UTF_8": "utf-8"
        })
