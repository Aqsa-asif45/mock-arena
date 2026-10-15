import ast
import os
import sys
from engine import run_match
from my_bot import MyBot
from opponents import HunterBot, CoreRusherBot, PickerBot

FORBID = {"os", "sys", "subprocess", "socket", "pickle", "threading"}
BANNED = {"open", "eval", "exec", "__import__"}


def static_fails(path):
    fails = []
    with open(path, encoding="utf8") as f:
        tree = ast.parse(f.read())
    for n in ast.walk(tree):
        mods = []
        if isinstance(n, ast.Import):
            mods = [a.name.split(".")[0] for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            mods = [(n.module or "").split(".")[0]]
        fails += [f"import {m}" for m in mods if m in FORBID]
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in BANNED:
            fails.append(f"call {n.func.id}")
    return fails


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    fails = static_fails(os.path.join(here, "my_bot.py"))
    r = run_match([MyBot, HunterBot, CoreRusherBot, PickerBot], seed=1)
    me = r["bots"][0]
    if me["illegal"]:
        fails.append(f"{me['illegal']} illegal action(s)")
    if me["exc"]:
        fails.append(f"{me['exc']} exception(s)")
    if me["slow"] or me["max_ms"] > 200:
        fails.append(f"decide() took {me['max_ms']} ms")
    print("PASS" if not fails else "FAIL: " + "; ".join(fails))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
