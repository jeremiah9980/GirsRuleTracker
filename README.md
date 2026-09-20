# GirsRuleTracker

12U C tournament tracker for the NCS Fastpitch **Girls Rule 65 Min Pool 6GG "C" and Open**
(event 13457, Sep 19–20, 2026 — Georgetown / Gatesville / Killeen, TX).

Open `index.html` (or serve the repo via GitHub Pages) to view:

- **Pool play standings** — final seeding with Gold (seeds 1–8) / Silver (seeds 9–16) bracket badges
- **Pool play results** — all 32 Saturday games with scores, searchable, with a team-highlight picker
  (defaults to Texas Venom 12U)
- **Sunday brackets** — Gold and Silver championship, elimination, and final rounds

Data lives in `data/tournament-12uc.js` / `.json`, scraped from the official NCS pages:
[Schedule](https://playncs.com/FASTPITCH/Events/Schedule/13457/girls-rule-65-min-pool-6gg-c-and-open?division=12U%20C) ·
[Standings](https://playncs.com/FASTPITCH/Events/Standings/13457/girls-rule-65-min-pool-6gg-c-and-open?division=12U%20C) ·
[Bracket](https://playncs.com/FASTPITCH/Events/Bracket/13457/girls-rule-65-min-pool-6gg-c-and-open?division=12U%20C)

## Refreshing scores

Bracket scores fill in on the NCS site as Sunday games finish. To pull the latest:

```bash
python3 -m pip install requests beautifulsoup4
python3 scripts/refresh.py
```

Then commit the updated `data/` files.
