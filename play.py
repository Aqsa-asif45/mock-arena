import argparse
from engine import run_match
from my_bot import MyBot
from opponents import HunterBot, CoreRusherBot, PickerBot

OPPONENTS = {c.__name__.lower().replace("bot", ""): c for c in (HunterBot, CoreRusherBot, PickerBot)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--seeds", type=int, default=0)
    ap.add_argument("--vs", default="hunter,corerusher,picker")
    ap.add_argument("--board", action="store_true")
    args = ap.parse_args()
    names = [n.strip().split(":")[-1].lower().replace("bot", "") for n in args.vs.split(",")]
    if len(names) != 3 or any(n not in OPPONENTS for n in names):
        ap.error(f"--vs needs 3 of: {', '.join(OPPONENTS)}")
    bots = [MyBot] + [OPPONENTS[n] for n in names]

    if args.seeds:
        rows = {}
        for s in range(args.seed, args.seed + args.seeds):
            for b in run_match(bots, s)["bots"]:
                row = rows.setdefault(b["id"], {"name": b["name"], "rank": 0, "wins": 0, "deaths": 0, "banked": 0.0})
                row["rank"] += b["placement"]
                row["wins"] += b["win"]
                row["deaths"] += b["deaths"]
                row["banked"] += b["banked"]
        n = args.seeds
        print(f"{'bot':<14}{'avg_rank':>9}{'wins':>6}{'deaths':>8}{'banked':>9}")
        for k in sorted(rows):
            r = rows[k]
            print(f"{r['name']:<14}{r['rank'] / n:>9.2f}{r['wins']:>6}{r['deaths'] / n:>8.2f}{r['banked'] / n:>9.2f}")
        return

    r = run_match(bots, args.seed, trace=args.board)
    if args.board:
        for f in r["frames"]:
            print(f + "\n")
    else:
        print("\n".join(r["log"]))
    print()
    for b in sorted(r["bots"], key=lambda b: b["placement"]):
        print(f"{b['placement']}. {b['name']:<12} score={b['score']} kills={b['kills']} "
              f"deaths={b['deaths']} banked={b['banked']} illegal={b['illegal']}")


if __name__ == "__main__":
    main()
