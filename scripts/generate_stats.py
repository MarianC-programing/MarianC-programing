#!/usr/bin/env python3
"""Genera assets/stats/github-stats.svg y assets/stats/top-langs.svg
usando la API GraphQL de GitHub a traves de la CLI `gh` (sin servicios externos).
Uso: python3 scripts/generate_stats.py <usuario>
"""
import json
import subprocess
import sys
from html import escape
from pathlib import Path

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "MarianC-programing"
OUT = Path(__file__).resolve().parent.parent / "assets" / "stats"

QUERY = """
query($login:String!){
  user(login:$login){
    name
    followers{totalCount}
    pullRequests{totalCount}
    issues{totalCount}
    contributionsCollection{ totalCommitContributions }
    repositories(first:100, ownerAffiliations:OWNER, isFork:false, privacy:PUBLIC){
      totalCount
      nodes{
        name
        stargazerCount
        languages(first:10, orderBy:{field:SIZE, direction:DESC}){
          edges{ size node{ name color } }
        }
      }
    }
  }
}
"""

BG, TITLE, TEXT, MUTED = "#1a1b27", "#70a5fd", "#a9b1d6", "#787c99"
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', Sans-Serif"


def fetch():
    res = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}", "-F", f"login={LOGIN}"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(res.stdout)["data"]["user"]


def stats_svg(u):
    repos = u["repositories"]["nodes"]
    rows = [
        ("Total Stars", sum(r["stargazerCount"] for r in repos)),
        ("Commits (last year)", u["contributionsCollection"]["totalCommitContributions"]),
        ("Pull Requests", u["pullRequests"]["totalCount"]),
        ("Issues", u["issues"]["totalCount"]),
        ("Public Repos", u["repositories"]["totalCount"]),
        ("Followers", u["followers"]["totalCount"]),
    ]
    h = 70 + len(rows) * 26
    name = escape(u["name"] or LOGIN)
    body = "".join(
        f'<text x="25" y="{75 + i * 26}" fill="{TEXT}" font-size="14">{escape(k)}</text>'
        f'<text x="270" y="{75 + i * 26}" fill="{TITLE}" font-size="14" font-weight="700" text-anchor="end">{v}</text>'
        for i, (k, v) in enumerate(rows)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="300" height="{h}" viewBox="0 0 300 {h}" font-family="{FONT}">
<rect width="300" height="{h}" rx="6" fill="{BG}"/>
<text x="25" y="38" fill="{TITLE}" font-size="18" font-weight="700">{name}'s GitHub Stats</text>
{body}
</svg>"""


def langs_svg(u):
    totals, colors = {}, {}
    for repo in u["repositories"]["nodes"]:
        for e in repo["languages"]["edges"]:
            n = e["node"]["name"]
            totals[n] = totals.get(n, 0) + e["size"]
            colors[n] = e["node"]["color"] or "#8b949e"
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:6]
    whole = sum(v for _, v in top) or 1
    w, bar_w, x, bars, legend = 300, 250, 25, "", ""
    for i, (n, v) in enumerate(top):
        pct = v / whole
        seg = bar_w * pct
        bars += f'<rect x="{x:.2f}" y="55" width="{seg:.2f}" height="10" fill="{colors[n]}"/>'
        x += seg
        col, row = i % 2, i // 2
        lx, ly = 25 + col * 130, 95 + row * 24
        legend += (
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="5" fill="{colors[n]}"/>'
            f'<text x="{lx + 16}" y="{ly}" fill="{TEXT}" font-size="12">{escape(n)} '
            f'<tspan fill="{MUTED}">{pct * 100:.1f}%</tspan></text>'
        )
    h = 95 + ((len(top) + 1) // 2) * 24 + 10
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">
<rect width="{w}" height="{h}" rx="6" fill="{BG}"/>
<text x="25" y="38" fill="{TITLE}" font-size="18" font-weight="700">Most Used Languages</text>
<clipPath id="c"><rect x="25" y="55" width="{bar_w}" height="10" rx="5"/></clipPath>
<g clip-path="url(#c)">{bars}</g>
{legend}
</svg>"""


def main():
    user = fetch()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "github-stats.svg").write_text(stats_svg(user), encoding="utf-8")
    (OUT / "top-langs.svg").write_text(langs_svg(user), encoding="utf-8")
    print("OK ->", OUT)


if __name__ == "__main__":
    main()
