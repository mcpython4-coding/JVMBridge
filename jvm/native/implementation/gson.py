from jvm.natives import bind_native, bind_annotation


class GsonBuilder:
    @staticmethod
    @bind_native("com/google/gson/GsonBuilder", "<init>()V")
    def init(method, stack, this):
        this.is_pretty_printing = False
        this.do_html_escaping = True

    @staticmethod
    @bind_native("com/google/gson/GsonBuilder", "setPrettyPrinting()Lcom/google/gson/GsonBuilder;")
    def setPrettyPrinting(method, stack, this):
        this.is_pretty_printing = True
        return this

    @staticmethod
    @bind_native("com/google/gson/GsonBuilder", "disableHtmlEscaping()Lcom/google/gson/GsonBuilder;")
    def disableHtmlEscaping(method, stack, this):
        this.do_html_escaping = False
        return this

    @staticmethod
    @bind_native("com/google/gson/GsonBuilder", "create()Lcom/google/gson/Gson;")
    def create(method, stack, this):
        return this


class JsonParser:
    @staticmethod
    @bind_native("com/google/gson/JsonParser", "<init>()V")
    def initJsonParse(method, stack, this):
        pass

