#!/usr/bin/env python3
"""Refresh Girls Rule 12U C tournament data from the NCS Fastpitch pages.

Re-scrapes the schedule, standings, and bracket for event 13457 (12U C)
and rewrites data/tournament-12uc.json and data/tournament-12uc.js.

Run from the repo root:
    python3 -m pip install requests beautifulsoup4
    python3 scripts/refresh.py
"""
from __future__ import annotations

import datetime
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

EVENT_ID = 13457
SLUG = "girls-rule-65-min-pool-6gg-c-and-open"
DIVISION = "12U C"
BASE = "https://playncs.com/FASTPITCH/Events"
UA = {"User-Agent": "Mozilla/5.0 (GirsRuleTracker refresh script)"}

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


def url(kind: str) -> str:
    return f"{BASE}/{kind}/{EVENT_ID}/{SLUG}?division={DIVISION.replace(' ', '%20')}"


def fetch(kind: str) -> BeautifulSoup:
    res = requests.get(url(kind), headers=UA, timeout=30)
    res.raise_for_status()
    return BeautifulSoup(res.text, "html.parser")


def clean(s: str | None) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def parse_standings(soup: BeautifulSoup) -> list[dict]:
    standings = []
    table = soup.find("table")
    if not table:
        return standings
    for tr in table.find_all("tr")[1:]:
        td = [clean(x.get_text()) for x in tr.find_all("td")]
        if len(td) >= 7:
            standings.append({
                "rank": int(td[0]), "team": td[1], "record": td[2],
                "ra": int(td[3]), "rd": int(td[4]), "rs": int(td[5]), "pts": int(td[6]),
            })
    return standings


def parse_schedule(soup: BeautifulSoup) -> list[dict]:
    games = []
    table = soup.find("table")
    if not table:
        return games
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 6:
            continue
        m = re.match(r"(\d+)\s+Game \d+", clean(tds[0].get_text()))
        num = m.group(1) if m else clean(tds[0].get_text())
        time = clean(tds[1].get_text())
        # the field cell duplicates its text; keep one copy when both halves match
        ftxt = clean(tds[2].get_text())
        half = len(ftxt) // 2
        field = ftxt[:half].strip() if ftxt[:half].strip() == ftxt[half:].strip() else ftxt

        def team_score(t: str):
            m = re.match(r"^(\d+)\s+(.*)$", t)
            return (int(m.group(1)), m.group(2)) if m else (None, t)

        s1, n1 = team_score(clean(tds[3].get_text()))
        s2, n2 = team_score(clean(tds[5].get_text()))
        games.append({
            "game": num, "time": time, "field": field,
            "home": n1, "away": n2, "home_score": s1, "away_score": s2,
            "score_label": clean(tds[4].get_text()),
        })
    return games


def parse_bracket_game(g) -> dict:
    info = g.find(class_="info")
    num = clean(info.find(class_="number").get_text()) if info and info.find(class_="number") else ""
    when = clean(info.find(class_="date-time").get_text()) if info else ""
    when = clean(when.replace(num, "").strip(" |"))
    place = clean(info.find(class_="place").get_text()) if info and info.find(class_="place") else ""
    out = {"num": num, "when": when, "place": place}
    for key, side in (("top", "team-top"), ("bottom", "team-bottom")):
        t = g.find("div", class_=side)
        seed = clean(t.find(class_="seed").get_text()) if t and t.find(class_="seed") else ""
        name = ""
        if t and t.find(class_="name"):
            sp = t.find(class_="name").find("span")
            name = clean(sp["title"]) if sp and sp.get("title") else clean(t.find(class_="name").get_text())
        score = clean(t.find(class_="score").get_text()) if t and t.find(class_="score") else ""
        winner = bool(t) and "winner" in (t.get("class") or [])
        out[key] = {"seed": seed, "name": name, "score": score, "winner": winner}
    return out


def parse_brackets(soup: BeautifulSoup) -> list[dict]:
    brackets = []
    for i, cont in enumerate(soup.find_all("div", class_="bracket-container")):
        sections = []
        for sec in cont.find_all("div", class_="bracket-section"):
            cls = sec.get("class", [])
            kind = ("winners" if "bracket-section-winners" in cls
                    else "losers" if "bracket-section-losers" in cls else "combined")
            nm = sec.find(class_="bracket-name")
            name = clean(nm.get_text()) if nm else ("Final" if kind == "combined" else "Bracket")
            games, seen = [], set()
            for g in sec.find_all("div", class_="game"):
                gid = g.get("data-id")
                if gid in seen:
                    continue
                seen.add(gid)
                games.append(parse_bracket_game(g))
            sections.append({"name": name, "kind": kind, "games": games})
        label = sections[0]["name"] if sections else f"Bracket {i + 1}"
        brackets.append({"label": "Gold" if "Champ" in label else "Silver", "sections": sections})
    return brackets


def main() -> int:
    print(f"Fetching NCS event {EVENT_ID} ({DIVISION})...")
    schedule = fetch("Schedule")
    standings = fetch("Standings")
    bracket = fetch("Bracket")

    data = {
        "event": {
            "id": EVENT_ID,
            "name": 'GIRLS RULE 65 MIN POOL 6GG "C" AND OPEN',
            "division": DIVISION,
            "dates": "Sep 19-20, 2026",
            "cities": "Georgetown / Gatesville / Killeen, TX",
            "director": "Maggie Stoecklein",
            "gate": "Gate fee cash only — Weekend pass $20, day pass $15, 12 & under free",
            "schedule_url": url("Schedule"),
            "standings_url": url("Standings"),
            "bracket_url": url("Bracket"),
            "scraped_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        },
        "standings": parse_standings(standings),
        "pool_games": parse_schedule(schedule),
        "brackets": parse_brackets(bracket),
    }

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "tournament-12uc.json").write_text(json.dumps(data, indent=1) + "\n")
    (DATA_DIR / "tournament-12uc.js").write_text(
        "window.TOURNAMENT = " + json.dumps(data, separators=(",", ":")) + ";\n")
    print(f"Wrote {len(data['standings'])} teams, {len(data['pool_games'])} pool games, "
          f"{len(data['brackets'])} brackets -> data/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
