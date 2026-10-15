from .geometry import cheb

DIRECTION_DELTAS = {
    "NORTH": (0, -1), "NORTHEAST": (1, -1), "EAST": (1, 0), "SOUTHEAST": (1, 1),
    "SOUTH": (0, 1), "SOUTHWEST": (-1, 1), "WEST": (-1, 0), "NORTHWEST": (-1, -1),
}


class Action:
    def __init__(self, kind, arg=None):
        self.kind, self.arg = kind, arg

    def __repr__(self):
        return self.kind if self.arg is None else f"{self.kind}({self.arg})"

    @staticmethod
    def move(direction):
        return Action("move", direction)

    @staticmethod
    def attack(bot_id):
        return Action("attack", bot_id)

    @staticmethod
    def shoot(direction):
        return Action("shoot", direction)

    @staticmethod
    def collect(item_id):
        return Action("collect", item_id)

    @staticmethod
    def defend():
        return Action("defend")

    @staticmethod
    def scan():
        return Action("scan")

    @staticmethod
    def ability(direction=None):
        return Action("ability", direction)


class Bot:
    ABILITY = None
    ROLE = None
    id = None

    @property
    def name(self):
        return type(self).__name__

    def decide(self, view):
        return Action.defend()


def toward(a, b):
    d = ((b[0] > a[0]) - (b[0] < a[0]), (b[1] > a[1]) - (b[1] < a[1]))
    return next((k for k, v in DIRECTION_DELTAS.items() if v == d), None)


def go(a, b):
    d = toward(a, b)
    return Action.move(d) if d else Action.defend()


def near(p, pts):
    return min(pts, key=lambda q: cheb(p, q))
