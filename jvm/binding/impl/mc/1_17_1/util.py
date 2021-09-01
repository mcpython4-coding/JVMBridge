from jvm.builtinwrapper import handler as builtin_handler


def clamp(x, a, b):
    return min(max(x, a), b)


@builtin_handler.bind_method("net/minecraft/util/Mth:m_14169_(FFF)I")
def hsvToRgb(h: float, s: float, v: float):
    i = int(h * 6) % 6
    f = h * 6 - i

    f1 = v * (1 - s)
    f2 = v * (1 - f * s)
    f3 = v * (1 - (1 - f) * s)

    if i == 0:
        r, g, b = v, f3, f1
    elif i == 1:
        r, g, b = f2, v, f1
    elif i == 2:
        r, g, b = f1, v, f3
    elif i == 3:
        r, g, b = f1, f2, v
    elif i == 4:
        r, g, b = f3, f1, v
    elif i == 5:
        r, g, b = v, f1, f2
    else:
        raise RuntimeError()

    return clamp(int(r * 255), 0, 255) << 16 | clamp(int(g * 255), 0, 255) << 8 | clamp(int(b * 255), 0, 255)

