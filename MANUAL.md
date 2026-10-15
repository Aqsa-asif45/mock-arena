# Vibe Wars – Poora Manual (Team ke liye)

> Yeh manual dono team members ke liye hai. Shuru se aakhir tak parho.

---

## 0. SABSE PEHLE: Bara idea samjho

Competition ke din kaam **2 hisson** mein hoga:

| Hissa | Kya | Kitni baar | Kyun |
|---|---|---|---|
| **BUILD** | Poora Scavenger bot **ek hi prompt** mein | 1 baar | Strategy pehle se mock arena mein test ho chuki hai. Pata hai kya kaam karta hai. |
| **IMPROVE** | Chhote fixes **ek ek karke** | Jitne time mile | Taake pata chale kaunsa fix fayda deta hai, kaunsa nuksan |

**Confusion clear:**
- ✅ Scavenger bot = **ek prompt** (Section 5 mein ready hai)
- ✅ Uske baad har naya change = **ek prompt, ek test**
- ❌ Ek saath 4–5 naye changes kabhi nahi. Mock mein dekha: result kharab hua aur pata nahi chala kyun.

---

## 1. Chhoti dictionary (yeh words baar baar aayenge)

| Word | Matlab |
|---|---|
| **Claude Code** | VS Code ke andar wala Claude. Files khud parhta, edit karta, commands chalata hai |
| **Prompt** | Jo hum Claude Code ko likh kar bolte hain |
| **Command** | Jo hum terminal mein khud likhte hain (jaise `python check.py`) |
| **Terminal** | VS Code mein neeche wali black window. Kholne ke liye: `` Ctrl + ` `` |
| **`/clear`** | Claude Code ki purani baatein mitata hai. Tokens bachte hain. Har naye kaam se pehle |
| **Seed** | Map ka number. Seed 7 = hamesha same map. Alag seed = alag map |
| **Avg rank** | Bot average kaunse number par aaya (1 = best, 4 = worst). **Jitna kam, utna acha** |
| **4th %** | Kitne maps mein bot last aaya. Jitna kam, utna acha |
| **Baseline** | Change se pehle ka number, taake compare kar sakein |
| **Backup** | Kaam karne wale bot ki copy (`backup_good.py`) |
| **check.py** | Jaldi test: bot valid hai? |
| **conformance.py** | Asli admission test. Fail = bot reject |

---

## 2. Din se pehle (checklist)

- [ ] Laptop charge + charger
- [ ] `python --version` → 3.9 ya upar
- [ ] VS Code + Claude Code extension installed, login ho chuka
- [ ] Yeh manual print ya phone mein
- [ ] Roles decide (neeche)

---

## 3. Roles

| Person | Naam | Kaam |
|---|---|---|
| **Driver** | ______ | Claude Code mein prompts likhta/paste karta hai |
| **Tester** | ______ | Terminal mein commands chalata hai, numbers kaagaz par likhta hai, **time dekhta hai** |

Tester ke paas "STOP" bolne ka haq hai jab time khatam ho ya bot toot jaye.

---

## 4. STEP 1 — Kit setup (9:00 – 9:15)

1. QR scan → GitHub page → **Code → Download ZIP**
2. ZIP ko **Desktop** par unzip karo
3. VS Code → **File → Open Folder** → kit folder chuno
4. Terminal kholo (`` Ctrl + ` ``) aur chalao:

```
python check.py
```
```
python play.py
```

✅ Dono chal gaye → aage barho
❌ Error → **haath uthao**, organizer ko bulao. Khud code mat chhedo.

5. Original bot ka backup:
```
cp my_bot.py backup_original.py
```

---

## 5. STEP 2 — Claude Code ko game samjhao (9:15 – 9:25)

**Claude Code** mein (Claude chat mein nahi) yeh paste karo:

### PROMPT 1 — Docs parho
```
Read docs/RULES.md, docs/BOT_SDK_CONTRACT.md and my_bot.py. Don't write code.
List in short bullets:
- exact view field names (self, enemies, resources, core, pads, walls, tags, base)
- exact Action syntax for every action
- everything that makes an action illegal
- how to set ROLE, ABILITY and buy()
- exact play.py and conformance.py command flags
```

**Tester ka kaam:** answer ko study guide se milao. Koi cheez ajeeb lage to note karo.

---

## 6. STEP 3 — Poora bot banao, EK prompt (9:25 – 9:45)

Pehle `/clear`, phir:

### PROMPT 2 — Scavenger bot
```
Write my_bot.py as a "Scavenger" bot using the exact view fields from the docs.
Class MyBot, ROLE="HAULER", ABILITY="DASH". Only vibe_sdk + stdlib. Deterministic
(no random/time, sort ties by distance then x then y).
Check every action for energy, range, board edges and cooldown before returning it.
Wrap decide() in try/except and always return a legal fallback.
Use vibe_sdk.geometry for walls and paths. Treat every list in view as possibly empty.

Priority rules, first match wins:
1. Adjacent enemy: if my hp >= its hp, attack. Else DASH away if possible, else defend.
2. Shoot enemy in straight line within 4 if its hp <= 10 and the line is clear.
3. Standing on a resource and hold not full: collect.
4. Carrying the Core: go to nearest uplink pad.
5. Go home to bank if hold full, or turns_left <= steps_home + 3, or cargo value >= 50.
6. Enemy Core planted and reachable: stand next to it.
7. Tag within 3 steps: go to it.
8. Core on ground, turn >= 26 and turns_left >= steps_to_pad + 4: go get it.
9. Go to best remembered resource by value / (distance + 1).
10. Explore: inner point farthest from visible enemies.

Remember seen resources and enemies across turns (reset if turn number goes down).
buy(): HAULER + POCKETS; add ARMOR if last placement >= 3 and credits allow.
Then run check.py and conformance.py and report pass/fail in 2 lines.
```

### Agar FAIL aaye
`/clear` mat karo (Claude ko error yaad rehna chahiye):
```
Fix the failure. Edit only what's needed. Run check.py and conformance.py again.
```
3 baar ke baad bhi fail → error ki **sirf aakhri 10 lines** copy karke:
```
check.py prints this: <paste>. Explain in 1 line and fix.
```

### Jab dono PASS
**Tester** foran:
```
cp my_bot.py backup_good.py
```
🎉 Ab aapke paas ek **submit karne laayak bot** hai. Baaki sab bonus hai.

---

## 7. STEP 4 — Testing ka tool banao (9:45 – 9:50)

`/clear`, phir:

### PROMPT 3 — Rank test script
```
Create rank_test.py (do not touch my_bot.py). It runs my bot in 30 matches
(seeds 1-30) using the kit's engine against the sparring/example opponents
(not copies of my bot). Print 1 line: avg placement, % of 4th places,
list of seeds where I was 4th. Then run it once.
```

**Tester:** jo number aaye woh likho. Yeh hai **BASELINE**.

```
Baseline: avg = ______   4th = ______%
```

Aage se tester khud chalayega (tokens zero):
```
python rank_test.py
```

---

## 8. STEP 5 — Improve, ek ek fix (9:50 – 10:15)

### Har fix ka 6-step loop

| Step | Kaun | Kya |
|---|---|---|
| 1 | Tester | Ek 4th wala seed ka log dekho: `python play.py --seed <number>` |
| 2 | Dono | Masla dhoondo: bot mara? cargo leke mara? deewar mein phansa? kuch nahi kiya? |
| 3 | Driver | `/clear` → fix prompt (neeche template) |
| 4 | Tester | `python check.py` → valid? |
| 5 | Tester | `python rank_test.py` → naya number |
| 6 | Dono | Faisla (neeche) |

### Fix prompt TEMPLATE
```
In my_bot.py: <ek chhota change>. Edit only that. Don't run tests.
```

### Faisla kaise karein
| Naya avg rank | Kya karo | Command |
|---|---|---|
| Baseline se **kam** (0.05+) | ✅ Rakho | `cp my_bot.py backup_good.py` → naya baseline likho |
| Baseline se **zyada** (0.05+) | ❌ Hatao | `cp backup_good.py my_bot.py` |
| Farq **0.05 se kam** | 🟡 Luck hai, hatao | `cp backup_good.py my_bot.py` |

### Log mein masla → ready fix prompts
| Log mein kya dikha | Fix prompt |
|---|---|
| Bot cargo leke mara, kuch bank nahi kiya | `In my_bot.py bank rule: also go home if an enemy is within 3 cells and cargo > 0. Edit only that. Don't run tests.` |
| Bot ek hi jagah phansa (`blocked` / `NO MOVE` baar baar) | `In my_bot.py: if my position didn't change for 2 turns, pick a different direction. Edit only that. Don't run tests.` |
| Bot aage peeche hil raha (flip-flop) | `In my_bot.py: keep the same target for 3 turns unless it disappears. Edit only that. Don't run tests.` |
| Bot bomb/airstrike mein mara | `In my_bot.py: add top rule: if my cell is inside a bomb/airstrike area that explodes next turn, move out or defend. Edit only that. Don't run tests.` |
| Bot ILLEGAL action kar raha | `My bot made an ILLEGAL action at turn X: <line>. Add the missing legality check. Edit only that.` |
| Bot bahut ghoomta, kuch collect nahi | `In my_bot.py: if no resource known and energy >= 40, use scan every 6 turns. Edit only that. Don't run tests.` |

**Ek baar mein ek hi.** Time kam ho to sirf top 2–3 problems.

---

## 9. STEP 6 — Freeze aur submit (10:15 – 10:30)

**10:15 — FREEZE.** Ab koi naya fix nahi.

**10:20 — Final check:**
```
cp backup_good.py my_bot.py
```
```
python check.py
```
```
python conformance.py
```
✅ Dono PASS → submit
❌ Fail → `cp backup_original.py my_bot.py` mat karo! Pichla PASS wala backup use karo.

**10:25 — Email:**
- Attachment: **`my_bot.py`** (backup file NAHI)
- Team name: ______
- Team ID: ______

---

## 10. Agar kuch galat ho jaye

| Masla | Kya karo |
|---|---|
| `check.py` fail | Prompt: `Fix check.py failure, edit only needed lines.` |
| `conformance.py` fail | Prompt: `conformance.py failed: <aakhri 10 lines>. Fix without changing strategy.` |
| Bot bilkul toot gaya | `cp backup_good.py my_bot.py` |
| "No such file" error | Galat folder mein ho. VS Code mein sahi folder kholo |
| `python` nahi chalta | `py` try karo (jaise `py check.py`) |
| Claude Code bahut lamba jawab de raha | `/clear` aur prompt ke aakhir mein likho: `Reply in 3 lines.` |
| 10:20 ho gaye aur kuch fail | Sabse aakhri PASS wala backup submit karo |

---

## 11. Saari commands ek jagah

| Kaam | Command |
|---|---|
| Bot valid? | `python check.py` |
| Admission test | `python conformance.py` |
| Rank test | `python rank_test.py` |
| Ek match ka log | `python play.py --seed 7` |
| 20 maps summary | `python play.py --seeds 20` |
| Backup save | `cp my_bot.py backup_good.py` |
| Backup wapas | `cp backup_good.py my_bot.py` |

(Asli kit ke flags PROMPT 1 ke answer se confirm karo.)

---

## 12. Golden rules
1. **Bot = 1 prompt. Improvement = 1 prompt per fix.**
2. **Har PASS ke baad backup.**
3. **Avg rank kam = acha.**
4. **Har naye kaam se pehle `/clear`** (fix fail ho to nahi).
5. **10:15 ke baad koi naya feature nahi.**
6. **`my_bot.py` mein os/sys/open/random/time NAHI.** Test scripts mein chalta hai.
7. **Guide aur engine mein farq ho → engine sahi hai.**
8. **Submit `my_bot.py`, backup nahi.**
