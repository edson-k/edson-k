import json
import math
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

USERNAME = os.environ.get("GITHUB_USERNAME", "edson-k")
TOKEN = os.environ.get("GH_STATS_TOKEN", "")
TOP_N = 10

OUTPUT = Path("assets/most-used-languages.svg")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

LANG_COLORS = {
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "PHP": "#4F5D95",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "SCSS": "#c6538c",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "Python": "#3572A5",
    "Vue": "#41b883",
    "Ruby": "#701516",
    "C++": "#f34b7d",
    "C": "#555555",
    "Java": "#b07219",
    "Go": "#00ADD8",
    "C#": "#178600",
    "Markdown": "#083fa1",
    "JSON": "#292929",
    "YAML": "#cb171e",
    "Vim Script": "#199f4b",
    "Rust": "#dea584",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
}

def fallback_color(name: str) -> str:
    h = abs(hash(name)) % 360
    return f"hsl({h}, 70%, 55%)"

def github_get(url: str):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("User-Agent", "lang-card-generator")

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_repos():
    repos = []
    page = 1

    while True:
        url = (
            "https://api.github.com/user/repos"
            f"?visibility=all&affiliation=owner&per_page=100&page={page}"
        )
        chunk = github_get(url)
        if not chunk:
            break
        repos.extend(chunk)
        page += 1

    return repos

def get_languages(owner: str, repo: str):
    url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    return github_get(url)

repos = get_repos()

totals = {}
for repo in repos:
    if repo.get("fork"):
        continue

    owner = repo["owner"]["login"]
    name = repo["name"]

    try:
        langs = get_languages(owner, name)
        for lang, value in langs.items():
            totals[lang] = totals.get(lang, 0) + value
    except Exception as e:
        print(f"Erro ao processar {owner}/{name}: {e}")

sorted_langs = sorted(totals.items(), key=lambda x: x[1], reverse=True)
top_langs = sorted_langs[:TOP_N]

total_bytes = sum(v for _, v in top_langs) or 1

items = []
for lang, value in top_langs:
    pct = (value / total_bytes) * 100
    color = LANG_COLORS.get(lang, fallback_color(lang))
    items.append({
        "name": lang,
        "pct": pct,
        "color": color
    })

# ===== VISUAL DO CARD =====
width = 700
height = 240
padding = 24

bg_color = "#1B1F2A"
border_color = "#CFCFD4"
title_color = "#5EA0FF"
text_color = "#D8E1EB"

title_y = 40
bar_x = padding
bar_y = 60
bar_width = width - padding * 2
bar_height = 14
radius = 7

left_x = 34
right_x = width // 2 + 15
legend_start_y = 105
row_gap = 32
dot_r = 5

def rect(x, y, w, h, fill, rx=0, stroke=None, stroke_width=None):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
    if rx:
        s += f' rx="{rx}"'
    if stroke:
        s += f' stroke="{stroke}"'
    if stroke_width:
        s += f' stroke-width="{stroke_width}"'
    s += '/>'
    return s

svg = []
svg.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')

# fundo
svg.append(rect(1, 1, width - 2, height - 2, bg_color, rx=10, stroke=border_color, stroke_width=2))

# título
svg.append(
    f'<text x="{padding}" y="{title_y}" fill="{title_color}" '
    f'font-family="Segoe UI, Arial, sans-serif" font-size="22" font-weight="700">'
    f'Most Used Languages</text>'
)

# barra colorida
svg.append(rect(bar_x, bar_y, bar_width, bar_height, "#2A3040", rx=radius))

current_x = bar_x
for i, item in enumerate(items):
    seg_w = round((item["pct"] / 100) * bar_width, 2)

    # evitar segmentozinhos invisíveis
    if seg_w < 6:
        seg_w = 6

    rx = radius if i == 0 else 0
    svg.append(rect(current_x, bar_y, seg_w, bar_height, item["color"], rx=rx))
    current_x += seg_w

# legenda em 2 colunas
half = math.ceil(len(items) / 2)

for idx, item in enumerate(items):
    col = 0 if idx < half else 1
    row = idx if col == 0 else idx - half

    x = left_x if col == 0 else right_x
    y = legend_start_y + row * row_gap

    svg.append(f'<circle cx="{x}" cy="{y}" r="{dot_r}" fill="{item["color"]}"/>')
    label = f'{escape(item["name"])} {item["pct"]:.2f}%'
    svg.append(
        f'<text x="{x + 14}" y="{y + 5}" fill="{text_color}" '
        f'font-family="Segoe UI, Arial, sans-serif" font-size="15">{label}</text>'
    )

svg.append("</svg>")

OUTPUT.write_text("\n".join(svg), encoding="utf-8")
print(f"Generated: {OUTPUT}")