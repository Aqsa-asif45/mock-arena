import sys
from engine import run_match
from my_bot import MyBot
from opponents import HunterBot, CoreRusherBot, PickerBot

BOTS = [MyBot, HunterBot, CoreRusherBot, PickerBot]


def stable(bots):
    return [{k: v for k, v in b.items() if k != "max_ms"} for b in bots]


def main():
    fails = []
    for seed in range(1, 11):
        a = run_match(BOTS, seed)
        b = run_match(BOTS, seed)
        me = a["bots"][0]
        if me["illegal"]:
            fails.append(f"seed {seed}: {me['illegal']} illegal action(s)")
        if me["exc"]:
            fails.append(f"seed {seed}: {me['exc']} exception(s)")
        if me["slow"] or me["max_ms"] > 200:
            fails.append(f"seed {seed}: decide() took {me['max_ms']} ms")
        if a["actions"] != b["actions"] or a["log"] != b["log"] or stable(a["bots"]) != stable(b["bots"]):
            fails.append(f"seed {seed}: non-deterministic")
    print("PASS" if not fails else "FAIL\n" + "\n".join(fails))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
