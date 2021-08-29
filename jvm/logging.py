
# You can override this methods from outside this file to do your own logging, but this is the way to go now...
# (Mcpython wraps them around its internal logger)
def warn(text: str):
    print("[JAVA][WARN]", warn)


def info(text: str):
    pass

