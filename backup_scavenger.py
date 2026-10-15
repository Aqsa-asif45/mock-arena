import heapq
from vibe_sdk import Bot, Action, DIRECTION_DELTAS, cheb
from vibe_sdk.geometry import line_clear, step_open

COST = {"move": 1, "collect": 2, "defend": 2, "attack": 5, "shoot": 6, "scan": 8, "ability": 10}
DIRS = sorted(DIRECTION_DELTAS.items())
INNER = [(4, 4), (7, 4), (7, 7), (4, 7)]
ALL = [(x, y) for y in range(12) for x in range(12)]


def add(p, d, k=1):
    return (p[0] + d[0] * k, p[1] + d[1] * k)


def inb(p):
    return 0 <= p[0] < 12 and 0 <= p[1] < 12


def ordered(c, pts):
    return [p for _, p in sorted((c["cost"][p], p) for p in dict.fromkeys(pts) if p in c["cost"])]


class MyBot(Bot):
    ABILITY = "DASH"
    ROLE = "HAULER"

    def __init__(self):
        self.reset()

    def reset(self):
        self.last_turn = 0
        self.res, self.enemy, self.tags = {}, {}, {}
        self.explore, self.last_scan = 0, -99
        self.carrying = self.my_plant = False
        self.walls, self.occ = set(), set()

    def decide(self, view):
        try:
            v = view
            if v["turn"] < self.last_turn:
                self.reset()
            self.last_turn = v["turn"]
            self.walls = {tuple(w) for w in v.get("walls", [])}
            self.occ = {(e["x"], e["y"]) for e in v.get("visible_enemies", [])}
            self.remember(v)
            c = self.map(v)
            for a in self.choose(v, c):
                if self.is_legal(v, a):
                    if a.kind == "scan":
                        self.last_scan = v["turn"]
                    return a
        except Exception:
            pass
        return self.fallback(view)

    def fallback(self, v):
        try:
            s = v["self"]
            if s["energy"] >= 2:
                return Action.defend()
            me = (s["x"], s["y"])
            for name, d in DIRS:
                if inb(add(me, d)) and add(me, d) not in self.walls:
                    return Action.move(name)
        except Exception:
            pass
        return Action.defend()

    def is_legal(self, v, a):
        s = v["self"]
        me = (s["x"], s["y"])
        if s["energy"] < COST.get(a.kind, 99):
            return False
        if a.kind == "move":
            return a.arg in DIRECTION_DELTAS and inb(add(me, DIRECTION_DELTAS[a.arg]))
        if a.kind == "attack":
            return any(e["id"] == a.arg and cheb(me, (e["x"], e["y"])) == 1 for e in v.get("visible_enemies", []))
        if a.kind == "shoot":
            return a.arg in DIRECTION_DELTAS
        if a.kind == "collect":
            if a.arg == "core":
                core = v.get("core", {})
                return core.get("state") == "loose" and (core.get("x"), core.get("y")) == me
            if any(g["id"] == a.arg and (g["x"], g["y"]) == me for g in v.get("tags", [])):
                return True
            return s["cargo_units"] < 5 and any(r["id"] == a.arg and (r["x"], r["y"]) == me
                                                for r in v.get("resources", []))
        if a.kind == "ability":
            if s.get("cooldown", 0) > 0 or a.arg not in DIRECTION_DELTAS:
                return False
            d = DIRECTION_DELTAS[a.arg]
            p1, p2 = add(me, d), add(me, d, 2)
            return (step_open(self.walls, me, p1) and step_open(self.walls, p1, p2)
                    and p1 not in self.occ and p2 not in self.occ)
        return True

    def remember(self, v):
        s, t = v["self"], v["turn"]
        me = (s["x"], s["y"])
        vis = {r["id"]: (r["x"], r["y"], r["value"]) for r in v.get("resources", [])}
        for rid in sorted(self.res):
            x, y, _ = self.res[rid]
            if rid not in vis and cheb(me, (x, y)) <= 3 and line_clear(self.walls, me, (x, y)):
                del self.res[rid]
        self.res.update(vis)
        for e in v.get("visible_enemies", []):
            self.enemy[e["id"]] = (e["x"], e["y"], t, e["hp"])
        self.tags = {g["id"]: (g["x"], g["y"], t + g["ttl"]) for g in v.get("tags", [])}
        core = v.get("core", {})
        if core.get("state") == "planted":
            if self.carrying:
                self.my_plant = True
        else:
            self.my_plant = False
        self.carrying = core.get("carrier") == s["id"]

    def map(self, v):
        s, t = v["self"], v["turn"]
        me = (s["x"], s["y"])
        tl = v.get("turns_left", 40 - t)
        vis = v.get("visible_enemies", [])
        danger = {}
        for e in vis:
            ep = (e["x"], e["y"])
            for q in ALL:
                d = cheb(ep, q)
                if d <= 2:
                    danger[q] = danger.get(q, 0) + (3, 2, 1)[d]
        ids = {e["id"] for e in vis}
        for eid in sorted(self.enemy):
            x, y, t0, _ = self.enemy[eid]
            if eid in ids or t - t0 > 3:
                continue
            for q in ALL:
                if cheb((x, y), q) <= 1:
                    danger[q] = danger.get(q, 0) + 1
        w = 1.0
        if s["rank"] == 1:
            w += 0.5
        if s["hp"] < 30:
            w += 1.5
        if s["rank"] == 4 and tl < 12:
            w -= 0.5
        cost, hops, first = self.dijkstra(me, danger, w)
        return {"me": me, "turn": t, "turns_left": tl, "cost": cost, "hops": hops, "first": first,
                "danger": danger, "base": [tuple(b) for b in s.get("base", [])],
                "enemies": [(e["x"], e["y"]) for e in vis]}

    def dijkstra(self, me, danger, w):
        cost, hops, first = {me: 0.0}, {me: 0}, {}
        heap, done = [(0.0, 0, me)], set()
        while heap:
            c, h, cur = heapq.heappop(heap)
            if cur in done:
                continue
            done.add(cur)
            for name, d in DIRS:
                nb = add(cur, d)
                if not step_open(self.walls, cur, nb):
                    continue
                nc = c + 1 + w * danger.get(nb, 0)
                if nb not in cost or nc < cost[nb]:
                    cost[nb], hops[nb] = nc, h + 1
                    first[nb] = name if cur == me else first[cur]
                    heapq.heappush(heap, (nc, h + 1, nb))
        return cost, hops, first

    def steps(self, c, targets):
        out, seen = [], set()
        for p in targets:
            name = c["first"].get(p)
            if name and name not in seen:
                seen.add(name)
                out.append(Action.move(name))
        return out

    def choose(self, v, c):
        for rule in (self.r_adjacent, self.r_shoot, self.r_pickup, self.r_carry, self.r_bank,
                     self.r_defuse, self.r_tag, self.r_core, self.r_resource, self.r_explore):
            acts = rule(v, c)
            if acts:
                return acts
        return [Action.defend()]

    def r_adjacent(self, v, c):
        s, me = v["self"], c["me"]
        adj = sorted((e for e in v.get("visible_enemies", []) if cheb(me, (e["x"], e["y"])) == 1),
                     key=lambda e: (e["hp"], e["id"]))
        if not adj:
            return []
        hp, out = s["hp"], []
        for e in adj:
            if e["hp"] <= 16 or (hp >= e["hp"] + 15 and hp > 35) or (
                    s["rank"] == 4 and c["turns_left"] <= 10 and hp >= e["hp"]):
                out.append(Action.attack(e["id"]))
        out += self.escape(v, c, [(e["x"], e["y"]) for e in adj])
        return out + [Action.defend()]

    def escape(self, v, c, foes):
        me, s, out = c["me"], v["self"], []

        def gap(p):
            return min(cheb(p, f) for f in foes)

        if s["energy"] >= 16 and s.get("cooldown", 0) == 0:
            dashes = []
            for name, d in DIRS:
                p1, p2 = add(me, d), add(me, d, 2)
                if (step_open(self.walls, me, p1) and step_open(self.walls, p1, p2)
                        and p1 not in self.occ and p2 not in self.occ and gap(p2) > gap(me)):
                    dashes.append((-gap(p2), name))
            out += [Action.ability(n) for _, n in sorted(dashes)]
        moves = []
        for name, d in DIRS:
            p = add(me, d)
            if step_open(self.walls, me, p) and p not in self.occ:
                moves.append((c["danger"].get(p, 0), -gap(p), name))
        return out + [Action.move(n) for _, _, n in sorted(moves)]

    def r_shoot(self, v, c):
        me, out = c["me"], []
        for e in sorted(v.get("visible_enemies", []), key=lambda e: (cheb(me, (e["x"], e["y"])), e["id"])):
            ep = (e["x"], e["y"])
            k = cheb(me, ep)
            if e["hp"] > 10 or not 1 <= k <= 4:
                continue
            for name, d in DIRS:
                if (add(me, d, k) == ep and line_clear(self.walls, me, ep)
                        and not any(add(me, d, i) in self.occ for i in range(1, k))):
                    out.append(Action.shoot(name))
        return out

    def r_pickup(self, v, c):
        s, me, out = v["self"], c["me"], []
        out += [Action.collect(g["id"]) for g in v.get("tags", []) if (g["x"], g["y"]) == me]
        if s["cargo_units"] < 5:
            out += [Action.collect(r["id"]) for r in v.get("resources", []) if (r["x"], r["y"]) == me]
        core = v.get("core", {})
        if core.get("state") == "loose" and (core["x"], core["y"]) == me and c["turn"] >= 26:
            out.append(Action.collect("core"))
        return out

    def r_carry(self, v, c):
        if v.get("core", {}).get("carrier") != v["self"]["id"]:
            return []
        return self.steps(c, ordered(c, [tuple(p) for p in v.get("pads", [])]))

    def r_bank(self, v, c):
        s, n = v["self"], v["self"]["cargo_units"]
        if n == 0:
            return []
        bases = ordered(c, c["base"])
        if not bases:
            return []
        home = c["hops"][bases[0]]
        if not (n >= 5 or c["turns_left"] <= home + 3 or s["cargo_value"] >= 50 or (c["turn"] >= 32 and n >= 2)):
            return []
        if c["me"] in c["base"]:
            return [Action.defend()]
        out = []
        if home >= 2 and s["energy"] >= 16 and s.get("cooldown", 0) == 0:
            name = c["first"][bases[0]]
            if c["hops"].get(add(c["me"], DIRECTION_DELTAS[name], 2)) == home - 2:
                out.append(Action.ability(name))
        return out + self.steps(c, bases)

    def r_defuse(self, v, c):
        core = v.get("core", {})
        if core.get("state") != "planted" or self.my_plant:
            return []
        pad, me = (core["x"], core["y"]), c["me"]
        if cheb(me, pad) <= 1:
            return [Action.defend()]
        ring = [(pad[0] + dx, pad[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
        return self.steps(c, ordered(c, ring))

    def r_tag(self, v, c):
        pts = [(x, y) for x, y, _ in self.tags.values()]
        return self.steps(c, [p for p in ordered(c, pts) if c["hops"][p] <= 3])

    def r_core(self, v, c):
        core = v.get("core", {})
        if core.get("state") != "loose" or c["turn"] < 26:
            return []
        q = (core["x"], core["y"])
        if q not in c["cost"]:
            return []
        mine = c["hops"][q]
        if any(cheb(q, f) <= mine for f in c["enemies"]):
            return []
        return self.steps(c, [q])

    def r_resource(self, v, c):
        s, me, tl = v["self"], c["me"], c["turns_left"]
        if s["cargo_units"] >= 5:
            return []
        best = []
        for rid in sorted(self.res):
            x, y, val = self.res[rid]
            p = (x, y)
            if p not in c["cost"] or p == me:
                continue
            h = c["hops"][p]
            if any(cheb(p, f) <= h - 2 for f in c["enemies"]):
                continue
            if h + min(cheb(p, b) for b in c["base"]) > tl:
                continue
            best.append((-val / (c["cost"][p] + 1), c["cost"][p], x, y))
        best.sort()
        return self.steps(c, [(x, y) for _, _, x, y in best[:3]])

    def r_explore(self, v, c):
        out = []
        if not self.res and v["self"]["energy"] >= 45 and c["turn"] - self.last_scan >= 6:
            out.append(Action.scan())
        for _ in range(4):
            if c["me"] == INNER[self.explore]:
                self.explore = (self.explore + 1) % 4
            if INNER[self.explore] in c["cost"]:
                break
            self.explore = (self.explore + 1) % 4
        return out + self.steps(c, [INNER[self.explore]])

    def buy(self, shop):
        try:
            if self.ROLE != "HAULER":
                return []
            credits, items = shop["credits"], []
            if credits >= 2:
                items.append("POCKETS")
                credits -= 2
            if credits >= 2 and shop.get("last_placement", 0) >= 3:
                items.append("ARMOR")
            return items
        except Exception:
            return None
