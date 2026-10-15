from vibe_sdk import Bot, Action, cheb, go, near


class HunterBot(Bot):
    def decide(self, v):
        s = v["self"]
        p, en = [s["x"], s["y"]], s["energy"]
        if v["visible_enemies"]:
            f = min(v["visible_enemies"], key=lambda f: cheb(p, [f["x"], f["y"]]))
            q = [f["x"], f["y"]]
            if cheb(p, q) == 1 and en >= 5:
                return Action.attack(f["id"])
            if en >= 1:
                return go(p, q)
        return Action.scan() if en >= 8 else Action.defend()


class CoreRusherBot(Bot):
    def decide(self, v):
        s, c = v["self"], v["core"]
        p, en = [s["x"], s["y"]], s["energy"]
        adj = [f for f in v["visible_enemies"] if cheb(p, [f["x"], f["y"]]) == 1]
        if adj and en >= 5:
            return Action.attack(adj[0]["id"])
        if c["carrier"] == s["id"]:
            return go(p, near(p, v["pads"]))
        if c["state"] == "loose":
            q = [c["x"], c["y"]]
            if cheb(p, q) <= 1 and en >= 2:
                return Action.collect("core")
            return go(p, q)
        return Action.scan() if en >= 8 else Action.defend()


class PickerBot(Bot):
    ROLE = "HAULER"

    def decide(self, v):
        s = v["self"]
        p, en, n = [s["x"], s["y"]], s["energy"], s["cargo_units"]
        if n and (n >= 3 or not v["resources"]):
            return Action.defend() if p in s["base"] else go(p, near(p, s["base"]))
        if v["resources"]:
            r = min(v["resources"], key=lambda r: cheb(p, [r["x"], r["y"]]))
            q = [r["x"], r["y"]]
            if cheb(p, q) <= 1 and en >= 2:
                return Action.collect(r["id"])
            return go(p, q)
        return Action.scan() if en >= 8 else Action.defend()
