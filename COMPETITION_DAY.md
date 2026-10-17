# COMPETITION DAY – Simple Manual

> Sunday ko sirf yeh file kholo. Upar se neeche chalo.

---

## 1. Teen baatein yaad rakho
1. **Sirf Claude Code** use karna hai (VS Code mein). Claude chat sirf backup hai.
2. **Bot = 1 prompt. Har fix = 1 prompt.**
3. **conformance PASS + behtar number = tabhi backup.**

⚠️ Sunday subah practice mat karna. Claude Pro ki limit bacha ke rakho.

---

## 2. Poora flow (ek nazar mein)
```
Setup → Prompt 1 → Prompt 2 → check → conformance → BACKUP
→ Prompt 3 (rank_test) → baseline likho → Prompt 4 (audit)
→ FIX LOOP x 2-3
→ 10:15 STOP → rank_test --start 31 → conformance → SUBMIT
```

---

## 3. Step by step

### STEP 1 – Setup (9:00)
1. QR → GitHub → **Code → Download ZIP** → Desktop par unzip
2. VS Code → **File → Open Folder** → kit folder
3. Terminal (`` Ctrl + ` ``):
```
python check.py
python play.py
cp my_bot.py backup_original.py
```
Error aaye → **haath uthao**.

### STEP 2 – PROMPT 1: docs parho (9:15)
```
Read docs/RULES.md, docs/BOT_SDK_CONTRACT.md and my_bot.py. Don't write code.
List in short bullets (under 30 lines):
- exact view field names (self, enemies, resources, crates, core, pads, walls, tags, base, bombs/airstrikes, item_pool, events)
- exact Action syntax for every action, and the exact id to collect the Core
- everything that makes an action illegal
- how ROLE, ABILITY, buy() are set
- whether the bot object is reused between matches
- exact flags for play.py, conformance.py and the sparring bot names
```
**Tester:** `docs/BOT_SDK_CONTRACT.md` khud bhi kholo (`Ctrl+Shift+V`, `Ctrl+F` → `view`). 3–4 field names kaagaz par likho.

### STEP 3 – PROMPT 2: poora bot (9:25)
`/clear` pehle.
```
Write my_bot.py as a "Scavenger" bot using the exact field names and Action syntax from the docs.
Class MyBot, ROLE="HAULER", ABILITY="DASH". Only vibe_sdk + stdlib. Deterministic
(no random/time, sort ties by distance then x then y, never iterate over sets).
Check every action for energy, range, board edges, cooldown and walls before returning it.
Collect only when standing exactly on the item. DASH only if both cells are free.
Wrap decide() in try/except and always return a legal fallback.
Use vibe_sdk.geometry for walls and paths. Treat every list in view as possibly empty.
If I am dead/respawning, return the safe fallback.

Memory: store only what the view showed me (resource positions, enemy last-seen position+turn).
Reset all memory when a new match starts (turn number is lower than or equal to last stored turn, or is the first turn).
Delete a remembered resource when I can see its cell and it is gone. Forget enemies after 3 turns.
Memory only helps choose where to go; never act on memory without checking the current view first.

Priority rules, first match wins:
0. My cell is inside a bomb/airstrike/orbital area that hits next turn: step out, else SHIELD/defend.
1. Adjacent enemy: if my hp >= its hp and energy >= 5, attack. Else DASH away if possible, else defend.
2. Shoot enemy in straight line within 4 if its hp <= 10 and the line is clear.
3. Standing on a resource and hold not full: collect. Standing on a crate: collect.
4. Holding an item: medpack if hp <= 35; railgun if 2+ enemies or a low-hp enemy on a clear line.
5. Carrying the Core: go to nearest uplink pad.
6. Go home to bank if hold full, or turns_left <= steps_home + 3, or cargo value >= 50.
7. Enemy Core planted and reachable: stand next to it.
8. Tag within 3 steps: go to it.
9. Core on ground, turn >= 26 and turns_left >= steps_to_pad + 4: go get it.
10. Crate within 3 steps and no enemy closer to it: go to it.
11. Go to best remembered resource by value / (distance + 1).
12. Explore: inner point farthest from visible enemies; prefer least-visited.
If my position didn't change for 2 turns, try a different direction.

buy(shop): role HAULER, items POCKETS; add ARMOR if last placement >= 3 and credits allow.
Return None on any error.
Then run check.py and conformance.py and report pass/fail in 2 lines.
```
**Fail ho to** (bina `/clear`):
```
Fix the failure. Edit only what's needed. Run check.py and conformance.py again.
```

### STEP 4 – PASS → BACKUP
```
python check.py
python conformance.py
cp my_bot.py backup_good.py
```
🎉 Ab submit karne laayak bot hai. Baaki sab bonus.

### STEP 5 – PROMPT 3: test file (9:45)
`/clear` pehle.
```
Create rank_test.py (do not touch my_bot.py). Use the kit's engine directly.
Run my bot in seat 0 for seeds 1-30 in 2 setups:
A) vs 3 different sparring/example opponents from the kit
B) vs the most aggressive opponents available (repeat one if needed)
Never use copies of my bot as opponents.
For each setup print 1 line: avg placement, % 4th, seeds where I was 4th.
Optional --start N to run seeds N..N+29. Must finish under 60 seconds. Run it once.
```
Phir khud:
```
python rank_test.py
```
**Baseline:** A = ____ B = ____ (4th % = ____)

### STEP 6 – PROMPT 4: legality audit
`/clear` pehle.
```
Audit my_bot.py against docs/RULES.md and docs/BOT_SDK_CONTRACT.md. Don't edit.
Answer OK or PROBLEM (with line number) in a table:
1. Every action checks energy cost first
2. Move/DASH never off board; DASH needs both cells free
3. Attack only adjacent visible enemy
4. Collect only when standing on the item; not when hold full
5. Ability/item only when ready and actually held
6. Item use matches item type and item_pool
7. Core collect uses the exact id from docs
8. Dead/respawning handled
9. Every view list may be empty; no KeyError
10. try/except returns legal fallback on every path
11. No random/time/os/sys/open/eval; only vibe_sdk + stdlib
12. Deterministic: no set iteration, ties sorted
13. Memory resets every new match; never acts on stale memory without checking the view
14. buy() valid names, max one KIT, within credits, None on error
15. decide() and buy() fast
16. Anything in the docs my bot ignores that could cause an illegal action
Reply only with the table.
```
PROBLEM aaye:
```
Fix audit problem #<number> only. Edit only that.
```
Phir `check.py` → `conformance.py` → backup.

### STEP 7 – FIX LOOP (9:55 – 10:15)

**a) Masla dhoondo:**
```
Run play.py for seeds <4th wale seeds, max 3>. Read the logs and list the top 3 reasons my bot placed 4th, 1 line each, with the turn as proof. Most common first. Don't edit.
```
Ya khud:
```
python play.py --seed <number> | Select-String "MYBOT|DIED|BANK|ILLEGAL"
```

| Log mein | Matlab |
|---|---|
| `ILLEGAL` | Legality missing → **sabse pehle fix** |
| `DIED` aur pehle koi `BANK` nahi | Cargo leke mara |
| Same position / `NO MOVE` baar baar | Phansa hua |
| Bahut `move`, koi `collect` nahi | Khali ghoom raha |
| Hits khaye, koi `attack` nahi | Fight back nahi kar raha |

**b) Ek fix:**
```
In my_bot.py: fix problem #1 only: <reason>. Edit only that. Don't run tests.
```

**c) Test:**
```
python check.py
python rank_test.py
```

**d) Faisla:**
| Result | Kya karo |
|---|---|
| Behtar (0.05+) | `python conformance.py` → PASS → `cp my_bot.py backup_good.py` |
| Kharab ya same | `cp backup_good.py my_bot.py` |

**Agla problem.** 10:15 par ruk jao, chahe list poori na ho.

### STEP 8 – FREEZE + SUBMIT (10:15)
```
cp backup_good.py my_bot.py
python check.py
python conformance.py
python rank_test.py --start 31
```
Naye maps par number thoda kharab ho sakta hai, normal hai. Bahut kharab (0.5+) ho → aakhri fix hatao.

**10:25 Email:** `my_bot.py` + team name + team ID. **Backup file NAHI.**

---

## 4. Aapke sawal – seedhe jawab

**Field names kya hain?**
`view` dabbe ke andar labels, jaise `view["self"]["hp"]`. Kit mein naam alag ho sakte hain (mock mein `"loose"`, asli mein shayad `"ON_GROUND"`). Galat naam = crash ya chupchaap galat behaviour. Isi liye **Prompt 1** aur `BOT_SDK_CONTRACT.md`.

**Memory legal hai?**
✅ Haan. Guide khud kehta hai: *"self.anything = remembers things between turns."* Ban sirf **random, time, files, internet** par hai. Memory sirf woh yaad rakhti hai jo view ne dikhaya.
2 khatre hain, dono Prompt 2 mein cover hain:
1. **Naye match mein purani memory** → har match par reset
2. **Purani memory par galat action** (jaise resource gayab ho chuka) → action se pehle current view check

**conformance kitni baar?** Jitni marzi. Free hai. Har rakhe gaye fix ke baad zaroor.

**Test file milegi?** Nahi. **Prompt 3** se banwani hai.

**Blood Moon / Smoke / Legendary?** Skip kiya: match mein sirf 1 baar hote hain, aur zyada code = zyada bugs. Time bache to:
```
In my_bot.py: during BLOOD_MOON, only attack if the enemy hp <= 24, otherwise avoid adjacent enemies. Edit only that. Don't run tests.
```

**Kya practice jaisa hi hoga?** Tareeqa same. Farq: asli game bara hai (items, events, shop), naam alag, opponents smart. Pehla goal: **9:45 tak PASS bot.**

---

## 5. Emergency
| Masla | Kya karo |
|---|---|
| Bot toot gaya | `cp backup_good.py my_bot.py` |
| 10:20 aur fail | Aakhri PASS backup submit |
| `python` nahi chalta | `py check.py` |
| "No such file" | Galat folder. VS Code mein kit folder kholo |
| Claude Code limit khatam | Claude chat: `my_bot.py` + error paste |
| WiFi slow | Phone hotspot |
