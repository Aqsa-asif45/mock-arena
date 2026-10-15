from engine import run_match
from my_bot import MyBot
from opponents import HunterBot, CoreRusherBot, PickerBot

SETUPS = {
    "A": [MyBot, HunterBot, CoreRusherBot, PickerBot],
    "C": [MyBot, HunterBot, HunterBot, CoreRusherBot],
}
N = 50
for name, bots in SETUPS.items():
    ranks, bad = [], []
    for s in range(51, 101):
        me = next(b for b in run_match(bots, s)["bots"] if b["id"] == 0)
        ranks.append(me["placement"])
        if me["placement"] == 4:
            bad.append(s)
    print(f"{name}: avg_rank={sum(ranks)/N:.2f}  4th={100*len(bad)/N:.0f}%  seeds={bad}")
