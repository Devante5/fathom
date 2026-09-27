#!/usr/bin/env python3
"""
Two gaps, seven calls: week-4 advanced box scores, and the talent data we have
never pulled.

WHY
---
1. advanced_box_scores_2026.csv stops at WEEK 3. pull_week4_results.py covered
   games and player box scores but not the advanced endpoint, so the site's
   efficiency numbers would be a week behind its ratings. That is precisely
   the inconsistency visible on the competitor's own page -- "Week 4 Power
   Rankings ... Current-season data through Week 3".

2. /talent and /recruiting/teams have never been pulled. They are the only
   real gap against the index lineup on that site (their TPi+ Talent Index).
   Both are free.

   Worth pulling; worth being sceptical of. Fathom already anchors on its own
   prior-season rating, which encodes talent AS IT ACTUALLY PERFORMED rather
   than as it was rated out of high school -- and that anchor was measured to
   help by 1.2-2.5 points of MAE in weeks 1-3 and to fade to nothing by week 6.
   Talent has to beat that, in that same window, to earn a place in anything.
   This pull gets the data so the question can be tested. It does not assume
   the answer.

COST
----
  1 call   /stats/game/advanced   year=2026 week=4
  5 calls  /talent                2022-2026
  5 calls  /recruiting/teams      2022-2026
Eleven calls total against the free tier.

HOW TO RUN
----------
Colab, one cell, same as the last one. It prompts for your key -- masked, not
saved into the notebook. Three CSVs download; attach all three back.
"""
import os
import sys
import time
import requests
import pandas as pd

BASE = "https://api.collegefootballdata.com"
YEAR, WEEK = 2026, 4
YEARS = [2022, 2023, 2024, 2025, 2026]

API_KEY = os.environ.get("CFBD_API_KEY", "").strip()
if not API_KEY:
    from getpass import getpass
    API_KEY = getpass("Paste your CFBD API key, then press Enter: ").strip()
if not API_KEY:
    sys.exit("No key entered. Re-run the cell and paste the key at the prompt.")
H = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}


def get(path, **params):
    for attempt in range(3):
        r = requests.get(f"{BASE}{path}", headers=H, params=params)
        if r.status_code == 200:
            return r.json()
        print(f"  {r.status_code} on {path} {params} (attempt {attempt+1})")
        time.sleep(2)
    return []


def flatten(d, prefix=""):
    """CFBD nests offense/defense dicts a few levels deep; flatten with _ joins."""
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, key + "_"))
        else:
            out[key] = v
    return out


# ------------------------------------------- 1. advanced box scores, week 4
rows = []
for g in get("/stats/game/advanced", year=YEAR, week=WEEK):
    r = {"gameId": g.get("gameId"), "season": g.get("season"),
         "seasonType": g.get("seasonType"), "week": WEEK,
         "team": g.get("team"), "opponent": g.get("opponent")}
    r.update(flatten(g.get("offense"), "off_"))
    r.update(flatten(g.get("defense"), "def_"))
    rows.append(r)
adv = pd.DataFrame(rows)
print(f"/stats/game/advanced  -> {len(adv)} team-games, {len(adv.columns)} columns")
adv.to_csv("week4_advanced_box_2026.csv", index=False)

# ------------------------------------------------------------- 2. talent
rows = []
for y in YEARS:
    d = get("/talent", year=y)
    for t in d:
        rows.append({"year": y, "team": t.get("team" if "team" in t else "school"),
                     "talent": t.get("talent")})
    print(f"/talent {y} -> {len(d)} teams")
tal = pd.DataFrame(rows)
tal.to_csv("team_talent_2022_2026.csv", index=False)

# -------------------------------------------------------- 3. recruiting
rows = []
for y in YEARS:
    d = get("/recruiting/teams", year=y)
    for t in d:
        rows.append({"year": y, "team": t.get("team"), "rank": t.get("rank"),
                     "points": t.get("points")})
    print(f"/recruiting/teams {y} -> {len(d)} teams")
rec = pd.DataFrame(rows)
rec.to_csv("team_recruiting_2022_2026.csv", index=False)

print(f"\nWrote week4_advanced_box_2026.csv ({len(adv)} rows), "
      f"team_talent_2022_2026.csv ({len(tal)} rows), "
      f"team_recruiting_2022_2026.csv ({len(rec)} rows)")
try:
    from google.colab import files
    for f in ("week4_advanced_box_2026.csv", "team_talent_2022_2026.csv",
              "team_recruiting_2022_2026.csv"):
        files.download(f)
except Exception:
    print("(not in Colab -- download the three files manually)")
