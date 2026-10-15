import random
import time
from collections import Counter
from vibe_sdk import Action, DIRECTION_DELTAS, cheb
from vibe_sdk.geometry import step_open, line_clear

SIZE, TURNS, OVERTIME, HP, EN = 12, 40, 32, 70, 50
COST = {"move": 1, "collect": 2, "defend": 2, "attack": 5, "shoot": 6, "scan": 8, "ability": 10}
ABIL_CD, SLOW_MS, WAVES = 6, 200, (1, 10, 18, 26)
CENTER = [(5, 5), (6, 5), (5, 6), (6, 6)]
PADS = [(5, 0), (11, 5), (6, 11), (0, 6)]
BASE_TL = [(0, 0), (1, 0), (0, 1), (1, 1)]


def rot(p, k=1):
    x, y = p
    for _ in range(k % 4):
        x, y = SIZE - 1 - y, x
    return (x, y)


def orbit(p):
    return [rot(p, k) for k in range(4)]


def on_board(p):
    return 0 <= p[0] < SIZE and 0 <= p[1] < SIZE


def add(p, d, k=1):
    return (p[0] + d[0] * k, p[1] + d[1] * k)


def valid_action(a):
    return isinstance(a, Action) and isinstance(a.kind, str) and (a.arg is None or isinstance(a.arg, (str, int)))


BASE = [[rot(c, k) for c in BASE_TL] for k in range(4)]
BASE_ALL = {c for row in BASE for c in row}
FIXED = set(orbit((2, 0))) | set(orbit((0, 2)))


def reachable(walls):
    seen, todo = {(0, 0)}, [(0, 0)]
    for p in todo:
        for d in DIRECTION_DELTAS.values():
            n = add(p, d)
            if n not in seen and step_open(walls, p, n):
                seen.add(n)
                todo.append(n)
    return len(seen) == SIZE * SIZE - len(walls)


def make_walls(rng):
    cands = [(x, y) for y in range(6) for x in range(6)
             if not (x <= 2 and y <= 2) and (x, y) not in PADS and (x, y) not in CENTER]
    while True:
        walls = set(FIXED)
        for c in cands:
            if rng.random() < 0.14:
                walls |= set(orbit(c))
        if reachable(walls):
            return walls


class Unit:
    def __init__(self, idx, bot):
        self.idx, self.bot, self.name = idx, bot, bot.name
        self.hauler = bot.ROLE == "HAULER"
        self.cap = 5 if self.hauler else 4
        self.pos, self.hp, self.en, self.cd = BASE[idx][0], HP, EN, 0
        self.cargo, self.score, self.kills, self.deaths, self.banked = [], 0.0, 0, 0, 0.0
        self.alive, self.respawn, self.prot, self.scanned, self.last_hit = True, 0, 0, False, -9
        self.carry, self.stance, self.dmg_by = False, None, []
        self.illegal, self.slow, self.exc, self.max_ms = 0, 0, 0, 0.0


class Match:
    def __init__(self, bots, seed, trace):
        self.seed, self.trace = seed, trace
        self.rng = random.Random(seed)
        self.walls = make_walls(self.rng)
        self.units = []
        for i, b in enumerate(bots):
            b = b() if isinstance(b, type) else b
            b.id = i
            self.units.append(Unit(i, b))
        self.res, self.tags, self.notes = [], [], {}
        self.core = {"state": "off", "pos": None, "carrier": None, "planter": None,
                     "planted": 0, "streak": 0, "respawn": 8}
        self.turn, self.uid, self.blood = 0, 100, False
        self.log, self.actions, self.frames, self.scanners = [], [], [], set()

    def new_id(self):
        self.uid += 1
        return self.uid

    def tag(self, i):
        return next((g for g in self.tags if g["id"] == i), None)

    def res_by_id(self, i):
        return next((r for r in self.res if r["id"] == i), None)

    def unit_at(self, p):
        return next((u for u in self.units if u.alive and u.pos == p), None)

    def ranks(self):
        order = sorted(self.units, key=lambda u: (-u.score, -u.kills, u.deaths, u.idx))
        return {u.idx: i + 1 for i, u in enumerate(order)}

    def gain(self, u, pts, reason):
        if self.turn >= OVERTIME:
            pts *= 2
        u.score += pts
        self.notes.setdefault(u.idx, []).append((pts, reason))
        return pts

    def line(self, u, act, res, notes=()):
        extra = "".join(f" ({p:+g} {r})" for p, r in notes)
        body = f"{act} {res}" if res else act
        self.log.append(f"T{self.turn:02d} {u.name.upper()} > {body}{extra}")

    def wave(self):
        taken = {r["pos"] for r in self.res}
        for _ in range(300):
            orb = orbit((self.rng.randrange(6), self.rng.randrange(6)))
            if all(p not in self.walls and p not in BASE_ALL and p not in PADS and p not in CENTER
                   and p not in taken for p in orb):
                v = self.rng.randint(10, 20)
                self.res += [{"id": self.new_id(), "pos": p, "value": v} for p in orb]
                return

    def start_turn(self):
        t = self.turn
        if t in WAVES:
            self.wave()
        c = self.core
        if c["state"] == "off" and t >= c["respawn"]:
            cell = self.rng.choice(CENTER)
            c.update(state="loose", pos=cell, carrier=None, streak=0, respawn=None)
            self.log.append(f"T{t:02d} CORE > SPAWN at {cell}")
        for u in self.units:
            if not u.alive and t >= u.respawn:
                taken = {v.pos for v in self.units if v.alive}
                u.pos = next(p for p in BASE[u.idx] if p not in taken)
                u.alive, u.hp, u.en, u.cargo, u.cd, u.prot = True, HP, EN, [], 0, 2
                self.line(u, "RESPAWN", f"at {u.pos}")

    def view(self, u):
        t, rank = self.turn, self.ranks()
        rad = 3 + (3 if u.scanned else 0)

        def seen(p):
            return cheb(p, u.pos) <= rad and line_clear(self.walls, u.pos, p)

        foes = []
        for v in self.units:
            if v is u or not v.alive:
                continue
            marks = []
            if self.core["carrier"] == v.idx:
                marks.append("CORE")
            if sum(v.cargo) >= 60:
                marks.append("CARGO")
            if v.last_hit == t - 1:
                marks.append("LOUD")
            if rank[v.idx] == 1:
                marks.append("CROWN")
            if marks or seen(v.pos):
                foes.append({"id": v.idx, "x": v.pos[0], "y": v.pos[1], "hp": v.hp, "marks": marks})
        cp = self.core["pos"]
        return {
            "turn": t,
            "turns_left": TURNS - t,
            "self": {"id": u.idx, "x": u.pos[0], "y": u.pos[1], "hp": u.hp, "energy": u.en,
                     "cargo_units": len(u.cargo), "cargo_value": round(sum(u.cargo), 2),
                     "cooldown": u.cd, "score": round(u.score, 2), "rank": rank[u.idx],
                     "alive": u.alive, "base": [list(p) for p in BASE[u.idx]]},
            "visible_enemies": foes,
            "resources": [{"id": r["id"], "x": r["pos"][0], "y": r["pos"][1], "value": r["value"]}
                          for r in self.res if seen(r["pos"])],
            "tags": [{"id": g["id"], "x": g["pos"][0], "y": g["pos"][1], "ttl": g["expires"] - t}
                     for g in self.tags],
            "core": {"x": cp[0] if cp else None, "y": cp[1] if cp else None,
                     "state": self.core["state"], "carrier": self.core["carrier"]},
            "pads": [list(p) for p in PADS],
            "walls": sorted(list(w) for w in self.walls),
            "board": {"width": SIZE, "height": SIZE},
        }

    def gather(self):
        acts = {}
        for u in self.units:
            if not u.alive:
                continue
            v = self.view(u)
            a, err = None, None
            t0 = time.perf_counter()
            try:
                a = u.bot.decide(v)
                if not valid_action(a):
                    err = "BAD ACTION"
            except Exception:
                err, u.exc = "EXCEPTION", u.exc + 1
            ms = (time.perf_counter() - t0) * 1000
            u.max_ms = max(u.max_ms, ms)
            if ms > SLOW_MS:
                err, u.slow = "TIMEOUT", u.slow + 1
            acts[u.idx] = (a, err)
        return acts

    def check(self, u, a):
        k = a.kind
        if k not in COST:
            return "UNKNOWN"
        if u.en < COST[k]:
            return "LOW ENERGY"
        if k in ("move", "shoot") and a.arg not in DIRECTION_DELTAS:
            return "BAD DIR"
        if k == "move" and not on_board(add(u.pos, DIRECTION_DELTAS[a.arg])):
            return "OFF BOARD"
        if k == "attack":
            if not isinstance(a.arg, int) or not 0 <= a.arg < len(self.units):
                return "BAD TARGET"
            tg = self.units[a.arg]
            if tg is u or not tg.alive:
                return "BAD TARGET"
            if cheb(u.pos, tg.pos) != 1:
                return "BAD RANGE"
        if k == "collect":
            if a.arg == "core":
                ok = self.core["state"] == "loose" and cheb(u.pos, self.core["pos"]) <= 1
                return None if ok else "NOTHING TO COLLECT"
            tg = self.tag(a.arg)
            if tg:
                return None if cheb(u.pos, tg["pos"]) <= 1 else "NOTHING TO COLLECT"
            r = self.res_by_id(a.arg)
            if r is None or cheb(u.pos, r["pos"]) > 1:
                return "NOTHING TO COLLECT"
            return "FULL HOLD" if len(u.cargo) >= u.cap else None
        if k == "ability":
            if u.bot.ABILITY is None:
                return "NO ABILITY"
            if u.cd > 0:
                return "COOLDOWN"
            if u.bot.ABILITY == "DASH":
                if a.arg not in DIRECTION_DELTAS:
                    return "BAD DIR"
                if not on_board(add(u.pos, DIRECTION_DELTAS[a.arg], 2)):
                    return "OFF BOARD"
        return None

    def collect(self, u, arg):
        c = self.core
        if arg == "core":
            if c["state"] != "loose":
                return "CONTESTED"
            c.update(state="carried", carrier=u.idx)
            u.carry = True
            return "CORE TAKEN"
        tg = self.tag(arg)
        if tg:
            self.tags.remove(tg)
            if u.idx in tg["killers"]:
                self.gain(u, 15, "killer tag")
            else:
                self.gain(u, 10, "denied tag")
            return "TAG"
        r = self.res_by_id(arg)
        if r is None:
            return "CONTESTED"
        self.res.remove(r)
        mult = 1.3 if any(v.alive and v is not u and cheb(v.pos, u.pos) <= 2 for v in self.units) else 1
        u.cargo.append(round(r["value"] * mult, 2))
        return f"GOT {u.cargo[-1]:g}"

    def hit(self, tg, dmg, src):
        if tg.prot:
            dmg = 0
        elif tg.stance == "defend":
            dmg //= 2
        elif tg.stance == "shield":
            dmg = int(dmg * 0.3)
        tg.hp -= dmg
        tg.last_hit = self.turn
        if dmg and src.idx not in tg.dmg_by:
            tg.dmg_by.append(src.idx)
        return dmg

    def resolve(self, acts):
        t = self.turn
        for u in self.units:
            u.stance, u.dmg_by = None, []
        self.scanners = set()
        legal, out = {}, {}
        for u in self.units:
            if not u.alive:
                continue
            a, err = acts[u.idx]
            why = err or self.check(u, a)
            self.actions.append((t, u.idx, str(a) if a is not None else err))
            if why:
                u.illegal += 1
                self.line(u, str(a) if a is not None else err, f"ILLEGAL ({why})")
                continue
            u.en -= COST[a.kind]
            if a.kind in ("attack", "shoot", "collect", "ability"):
                u.prot = 0
            if a.kind == "ability":
                u.cd = ABIL_CD
                if u.bot.ABILITY == "SHIELD":
                    u.stance = "shield"
            if a.kind == "defend":
                u.stance = "defend"
            if a.kind == "scan":
                self.scanners.add(u.idx)
            legal[u.idx] = a

        occ = {u.pos for u in self.units if u.alive}
        for i in sorted(legal):
            if legal[i].kind == "collect":
                out[i] = self.collect(self.units[i], legal[i].arg)

        intent = {}
        for i in sorted(legal):
            a, u = legal[i], self.units[i]
            if a.kind == "move":
                dest = add(u.pos, DIRECTION_DELTAS[a.arg])
                intent[i] = dest if dest not in occ and step_open(self.walls, u.pos, dest) else None
            elif a.kind == "ability" and u.bot.ABILITY == "DASH":
                d = DIRECTION_DELTAS[a.arg]
                mid, dest = add(u.pos, d), add(u.pos, d, 2)
                ok = (mid not in occ and dest not in occ and step_open(self.walls, u.pos, mid)
                      and step_open(self.walls, mid, dest))
                intent[i] = dest if ok else None
        cnt = Counter(v for v in intent.values() if v)
        for i, dest in intent.items():
            if dest and cnt[dest] == 1:
                self.units[i].pos = dest
                out[i] = f"-> {dest[0]},{dest[1]}"
            else:
                out[i] = "NO MOVE"

        for i in sorted(legal):
            if legal[i].kind == "attack":
                tg = self.units[legal[i].arg]
                out[i] = f"HIT {tg.idx} {self.hit(tg, self.rng.randint(16, 24), self.units[i])}"

        for i in sorted(legal):
            a = legal[i]
            if a.kind != "shoot":
                continue
            u = self.units[i]
            out[i] = "MISS"
            for k in range(1, 5):
                cell = add(u.pos, DIRECTION_DELTAS[a.arg], k)
                if not on_board(cell) or cell in self.walls:
                    break
                tg = self.unit_at(cell)
                if tg:
                    out[i] = f"HIT {tg.idx} {self.hit(tg, self.rng.randint(10, 14), u)}"
                    break

        for i, a in legal.items():
            out.setdefault(i, {"defend": "GUARD", "scan": "VISION+3 next turn"}.get(
                a.kind, "SHIELD" if a.kind == "ability" else "OK"))

        c = self.core
        if c["state"] == "carried":
            cu = self.units[c["carrier"]]
            c["pos"] = cu.pos
            if cu.pos in PADS:
                c.update(state="planted", planter=cu.idx, planted=t, streak=0, carrier=None)
                cu.carry = False
                self.log.append(f"T{t:02d} CORE > PLANTED at {cu.pos} by {cu.name.upper()}")

        for u in self.units:
            if not u.alive or u.hp > 0:
                continue
            u.alive, u.hp, u.deaths, u.respawn, u.scanned = False, 0, u.deaths + 1, t + 3, False
            killers = list(u.dmg_by)
            for k in killers:
                kl = self.units[k]
                kl.kills += 1
                self.gain(kl, 25, f"kill {u.name.upper()}")
                if kl.hauler:
                    self.gain(kl, -10, "hauler kill penalty")
                if not self.blood:
                    self.blood = True
                    self.gain(kl, 20, "first blood")
            if killers:
                self.tags.append({"id": self.new_id(), "pos": u.pos, "expires": t + 6, "killers": killers})
            self.res += [{"id": self.new_id(), "pos": u.pos, "value": v} for v in u.cargo]
            u.cargo = []
            if u.carry:
                c.update(state="loose", pos=u.pos, carrier=None)
                u.carry = False
            self.line(u, "DIED", f"respawn T{t + 3:02d}")

        for i in sorted(legal):
            self.line(self.units[i], str(legal[i]), out[i], self.notes.pop(i, ()))

    def end_turn(self):
        t = self.turn
        for u in self.units:
            if u.alive and u.cargo and u.pos in BASE[u.idx]:
                n = len(u.cargo)
                mult = (1.5 if n >= 4 else 1.25 if n >= 3 else 1) if u.hauler else 1
                val = sum(u.cargo) * mult
                u.cargo = []
                u.banked += self.gain(u, val, f"BANK {n} units")

        c = self.core
        if c["state"] == "planted":
            near = [v for v in self.units if v.alive and v.idx != c["planter"] and cheb(v.pos, c["pos"]) <= 1]
            c["streak"] = c["streak"] + 1 if near else 0
            if c["streak"] >= 2:
                for v in near:
                    self.gain(v, 40, "core defused")
                self.log.append(f"T{t:02d} CORE > DEFUSED")
                c.update(state="off", pos=None, carrier=None, respawn=t + 4)
            elif t - c["planted"] >= 3:
                self.gain(self.units[c["planter"]], 60, "core survived")
                self.log.append(f"T{t:02d} CORE > SURVIVED")
                c.update(state="off", pos=None, carrier=None, respawn=t + 4)

        self.tags = [g for g in self.tags if g["expires"] > t]
        for u in self.units:
            u.scanned = u.alive and u.idx in self.scanners
            if u.alive:
                u.en = min(EN, u.en + (10 if t >= OVERTIME else 5))
                u.cd = max(0, u.cd - 1)
                u.prot = max(0, u.prot - 1)
        for u in self.units:
            if self.notes.get(u.idx):
                self.line(u, "EVENT", "", self.notes.pop(u.idx))

    def render(self):
        g = [["."] * SIZE for _ in range(SIZE)]
        for p in BASE_ALL:
            g[p[1]][p[0]] = "_"
        for p in PADS:
            g[p[1]][p[0]] = "P"
        for x, y in self.walls:
            g[y][x] = "#"
        for r in self.res:
            g[r["pos"][1]][r["pos"][0]] = "$"
        for tg in self.tags:
            g[tg["pos"][1]][tg["pos"][0]] = "T"
        if self.core["pos"]:
            g[self.core["pos"][1]][self.core["pos"][0]] = "C"
        for u in self.units:
            if u.alive:
                g[u.pos[1]][u.pos[0]] = str(u.idx)
        return "\n".join("".join(row) for row in g)

    def results(self):
        rk = self.ranks()
        bots = [{"id": u.idx, "name": u.name, "score": round(u.score, 2), "kills": u.kills,
                 "deaths": u.deaths, "banked": round(u.banked, 2), "placement": rk[u.idx],
                 "win": rk[u.idx] == 1, "illegal": u.illegal, "slow": u.slow, "exc": u.exc,
                 "max_ms": round(u.max_ms, 2)} for u in self.units]
        return {"seed": self.seed, "bots": bots, "log": self.log, "actions": self.actions,
                "frames": self.frames}

    def run(self):
        for t in range(1, TURNS + 1):
            self.turn = t
            mark = len(self.log)
            self.start_turn()
            self.resolve(self.gather())
            self.end_turn()
            if self.trace:
                self.frames.append(self.render() + "\n" + "\n".join(self.log[mark:]))
        return self.results()


def run_match(bots, seed, trace=False):
    return Match(bots, seed, trace).run()
