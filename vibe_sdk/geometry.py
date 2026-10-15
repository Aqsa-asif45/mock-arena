import math


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def step_open(walls, a, b, size=12):
    if not (0 <= b[0] < size and 0 <= b[1] < size) or b in walls:
        return False
    dx, dy = b[0] - a[0], b[1] - a[1]
    return not (dx and dy and (a[0] + dx, a[1]) in walls and (a[0], a[1] + dy) in walls)


def line_clear(walls, a, b):
    n = cheb(a, b)
    for i in range(1, n):
        p = (math.floor(a[0] + (b[0] - a[0]) * i / n + 0.5), math.floor(a[1] + (b[1] - a[1]) * i / n + 0.5))
        if p in walls:
            return False
    return True
