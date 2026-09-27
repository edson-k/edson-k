import json
import math
import os
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape


# ============================================================
# CONFIGURAÇÃO
# ============================================================

USERNAME = os.environ.get("GITHUB_USERNAME", "edson-k")
TOKEN = os.environ.get("GH_STATS_TOKEN", "")

# Quantas linguagens mostrar no card
TOP_N = 10

# Owners que SERÃO contabilizados.
# Qualquer owner fora daqui será ignorado.
INCLUDE_OWNERS = {
    "edson-k",
    "RedBerryLTDA",
    "BanzaiAnimes",
}

# Repositórios específicos que você NÃO quer contabilizar.
#
# Sempre use:
# "OWNER/NOME-DO-REPOSITORIO"
#
EXCLUDE_REPOS = {
    # Exemplos:
    # "edson-k/projeto-antigo",
    # "RedBerryLTDA/testes",
    # "BanzaiAnimes/projeto-legado",
}

# Linguagens que você queira ignorar completamente.
#
# Eu recomendo deixar vazio por enquanto.
# Primeiro vamos descobrir de onde está vindo aquele C.
EXCLUDE_LANGUAGES = {
    # "C",
    # "Shell",
}

# Ignorar forks?
IGNORE_FORKS = True

# Arquivo gerado
OUTPUT = Path("assets/most-used-languages.svg")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# CORES DAS LINGUAGENS
# ============================================================

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
    "Dart": "#00B4AB",
    "Lua": "#000080",
    "PowerShell": "#012456",
    "Batchfile": "#C1F12E",
    "EJS": "#a91e50",
}


def fallback_color(name: str) -> str:
    """
    Gera uma cor consistente para linguagens que não estiverem
    na tabela LANG_COLORS.
    """

    # Não usamos hash() diretamente porque ele pode variar
    # entre execuções do Python.
    value = sum(ord(char) for char in name)
    hue = value % 360

    return f"hsl({hue}, 65%, 55%)"


# ============================================================
# GITHUB API
# ============================================================

def github_get(url: str):
    req = urllib.request.Request(url)

    req.add_header(
        "Accept",
        "application/vnd.github+json"
    )

    req.add_header(
        "X-GitHub-Api-Version",
        "2022-11-28"
    )

    req.add_header(
        "User-Agent",
        "edson-k-language-card"
    )

    if TOKEN:
        req.add_header(
            "Authorization",
            f"Bearer {TOKEN}"
        )

    with urllib.request.urlopen(req) as response:
        return json.loads(
            response.read().decode("utf-8")
        )


def get_repos():
    """
    Busca todos os repositórios aos quais o PAT possui acesso:
    - próprios
    - organizações
    - colaborador

    Depois filtramos usando INCLUDE_OWNERS.
    """

    repos = []
    page = 1

    while True:
        url = (
            "https://api.github.com/user/repos"
            "?visibility=all"
            "&affiliation=owner,collaborator,organization_member"
            "&sort=full_name"
            "&direction=asc"
            "&per_page=100"
            f"&page={page}"
        )

        chunk = github_get(url)

        if not chunk:
            break

        repos.extend(chunk)

        print(
            f"Página {page}: "
            f"{len(chunk)} repositórios encontrados"
        )

        page += 1

    return repos


def get_languages(owner: str, repo: str):
    """
    Retorna quantidade de bytes por linguagem
    segundo o GitHub Linguist.
    """

    url = (
        f"https://api.github.com/repos/"
        f"{owner}/{repo}/languages"
    )

    return github_get(url)


# ============================================================
# COLETA DAS LINGUAGENS
# ============================================================

print()
print("=" * 70)
print("GENERATE LANGUAGE CARD")
print("=" * 70)
print()

if not TOKEN:
    print("ATENÇÃO: GH_STATS_TOKEN não foi informado.")
    print("Repositórios privados provavelmente não serão encontrados.")
    print()


repos = get_repos()

print()
print(
    f"Total retornado pela API: {len(repos)} repositórios"
)
print()

totals = {}

processed_repos = []
ignored_repos = []

# Isso ajuda a descobrir qual repositório
# está dominando uma determinada linguagem.
language_sources = {}


for repo in repos:

    owner = repo["owner"]["login"]
    name = repo["name"]
    full_name = repo["full_name"]

    # --------------------------------------------------------
    # OWNER
    # --------------------------------------------------------

    if owner not in INCLUDE_OWNERS:
        print(
            f"IGNORADO OWNER: {full_name}"
        )

        ignored_repos.append(
            (full_name, "owner")
        )

        continue

    # --------------------------------------------------------
    # FORK
    # --------------------------------------------------------

    if IGNORE_FORKS and repo.get("fork"):
        print(
            f"IGNORADO FORK: {full_name}"
        )

        ignored_repos.append(
            (full_name, "fork")
        )

        continue

    # --------------------------------------------------------
    # REPOSITÓRIO EXCLUÍDO
    # --------------------------------------------------------

    if full_name in EXCLUDE_REPOS:
        print(
            f"IGNORADO REPO: {full_name}"
        )

        ignored_repos.append(
            (full_name, "exclude")
        )

        continue

    # --------------------------------------------------------
    # BUSCAR LINGUAGENS
    # --------------------------------------------------------

    try:

        langs = get_languages(
            owner,
            name
        )

        processed_repos.append(
            full_name
        )

        print()
        print(
            f"📦 {full_name}"
        )

        if repo.get("private"):
            print(
                "   🔒 PRIVATE"
            )
        else:
            print(
                "   🌎 PUBLIC"
            )

        if not langs:
            print(
                "   Sem linguagens detectadas."
            )

        for lang, value in langs.items():

            if lang in EXCLUDE_LANGUAGES:
                print(
                    f"   IGNORADA: {lang}"
                )

                continue

            print(
                f"   {lang:<20} "
                f"{value:>12,} bytes"
            )

            totals[lang] = (
                totals.get(lang, 0)
                + value
            )

            if lang not in language_sources:
                language_sources[lang] = []

            language_sources[lang].append(
                (
                    full_name,
                    value
                )
            )

            # ------------------------------------------------
            # DEBUG ESPECIAL PARA C
            # ------------------------------------------------

            if lang == "C":

                print(
                    f"   ⚠️  C ENCONTRADO: "
                    f"{value:,} bytes"
                )

    except Exception as error:

        print()
        print(
            f"❌ ERRO: {full_name}"
        )

        print(
            f"   {error}"
        )


# ============================================================
# RELATÓRIO
# ============================================================

print()
print("=" * 70)
print("RESUMO")
print("=" * 70)

print()
print(
    f"Processados: {len(processed_repos)}"
)

print(
    f"Ignorados: {len(ignored_repos)}"
)

print()


# ============================================================
# DESCOBRIR DE ONDE VEM O C
# ============================================================

if "C" in language_sources:

    print()
    print("=" * 70)
    print("⚠️  REPOSITÓRIOS COM C")
    print("=" * 70)

    c_sources = sorted(
        language_sources["C"],
        key=lambda item: item[1],
        reverse=True
    )

    for repo_name, value in c_sources:

        print(
            f"{repo_name:<50} "
            f"{value:>15,} bytes"
        )

    print()


# ============================================================
# TOTAL POR LINGUAGEM
# ============================================================

sorted_all_languages = sorted(
    totals.items(),
    key=lambda item: item[1],
    reverse=True
)

grand_total = sum(
    value
    for _, value in sorted_all_languages
)

print()
print("=" * 70)
print("TOTAL POR LINGUAGEM")
print("=" * 70)
print()

for lang, value in sorted_all_languages:

    pct = (
        value / grand_total * 100
        if grand_total
        else 0
    )

    print(
        f"{lang:<20} "
        f"{value:>15,} bytes "
        f"{pct:>7.2f}%"
    )


# ============================================================
# TOP N
# ============================================================

top_languages = sorted_all_languages[
    :TOP_N
]

displayed_total = sum(
    value
    for _, value in top_languages
)

items = []

for lang, value in top_languages:

    # Percentual REAL considerando TODAS as linguagens.
    real_pct = (
        value / grand_total * 100
        if grand_total
        else 0
    )

    # Percentual usado somente para desenhar a barra,
    # normalizando os TOP_N para ocupar 100% da largura.
    bar_pct = (
        value / displayed_total * 100
        if displayed_total
        else 0
    )

    color = LANG_COLORS.get(
        lang,
        fallback_color(lang)
    )

    items.append({
        "name": lang,
        "value": value,
        "pct": real_pct,
        "bar_pct": bar_pct,
        "color": color,
    })


# ============================================================
# CARD SVG
# ============================================================

# Quantidade de linhas necessárias
half = math.ceil(
    len(items) / 2
)

rows = half


# ------------------------------------------------------------
# CONFIGURAÇÃO VISUAL
# ------------------------------------------------------------

width = 520

padding = 26

bg_color = "#1B1F2A"
border_color = "#C8CBD0"

title_color = "#6CA6FF"
text_color = "#D8E1EB"

title_y = 40


# ------------------------------------------------------------
# BARRA
# ------------------------------------------------------------

bar_x = 26
bar_y = 60

bar_width = (
    width - 52
)

bar_height = 10
bar_radius = 5


# ------------------------------------------------------------
# LEGENDA
# ------------------------------------------------------------

left_x = 32
right_x = 275

legend_start_y = 102

row_gap = 30

dot_r = 5

bottom_padding = 24


# ------------------------------------------------------------
# ALTURA AUTOMÁTICA
# ------------------------------------------------------------

if rows > 0:

    last_row_y = (
        legend_start_y
        + ((rows - 1) * row_gap)
    )

    height = (
        last_row_y
        + bottom_padding
        + 10
    )

else:

    height = 120


# ============================================================
# HELPERS SVG
# ============================================================

def rect(
    x,
    y,
    w,
    h,
    fill,
    rx=0,
    stroke=None,
    stroke_width=None,
):

    element = (
        f'<rect '
        f'x="{x}" '
        f'y="{y}" '
        f'width="{w}" '
        f'height="{h}" '
        f'fill="{fill}"'
    )

    if rx:

        element += (
            f' rx="{rx}"'
        )

    if stroke:

        element += (
            f' stroke="{stroke}"'
        )

    if stroke_width:

        element += (
            f' stroke-width="{stroke_width}"'
        )

    element += "/>"

    return element


def shorten(
    text: str,
    max_length: int = 18,
):

    if len(text) <= max_length:
        return text

    return (
        text[:max_length - 1]
        + "…"
    )


# ============================================================
# GERAR SVG
# ============================================================

svg = []


svg.append(
    f'<svg '
    f'width="{width}" '
    f'height="{height}" '
    f'viewBox="0 0 {width} {height}" '
    f'xmlns="http://www.w3.org/2000/svg">'
)


# ------------------------------------------------------------
# FUNDO
# ------------------------------------------------------------

svg.append(
    rect(
        1,
        1,
        width - 2,
        height - 2,
        bg_color,
        rx=8,
        stroke=border_color,
        stroke_width=1,
    )
)


# ------------------------------------------------------------
# TÍTULO
# ------------------------------------------------------------

svg.append(
    f'<text '
    f'x="{padding}" '
    f'y="{title_y}" '
    f'fill="{title_color}" '
    f'font-family="Segoe UI, Arial, sans-serif" '
    f'font-size="19" '
    f'font-weight="700">'
    f'Linguagens mais usadas'
    f'</text>'
)


# ------------------------------------------------------------
# CLIP DA BARRA
# ------------------------------------------------------------

svg.append(
    f'''
<defs>
    <clipPath id="barClip">
        <rect
            x="{bar_x}"
            y="{bar_y}"
            width="{bar_width}"
            height="{bar_height}"
            rx="{bar_radius}"
        />
    </clipPath>
</defs>
'''
)


# ------------------------------------------------------------
# FUNDO DA BARRA
# ------------------------------------------------------------

svg.append(
    rect(
        bar_x,
        bar_y,
        bar_width,
        bar_height,
        "#30363D",
        rx=bar_radius,
    )
)


# ------------------------------------------------------------
# BARRA COLORIDA
# ------------------------------------------------------------

current_x = bar_x

for item in items:

    segment_width = (
        item["bar_pct"]
        / 100
        * bar_width
    )

    svg.append(
        f'<rect '
        f'x="{current_x:.2f}" '
        f'y="{bar_y}" '
        f'width="{segment_width:.2f}" '
        f'height="{bar_height}" '
        f'fill="{item["color"]}" '
        f'clip-path="url(#barClip)"'
        f'/>'
    )

    current_x += (
        segment_width
    )


# ------------------------------------------------------------
# ITENS
# ------------------------------------------------------------

for index, item in enumerate(items):

    if index < half:

        column = 0
        row = index

    else:

        column = 1
        row = (
            index - half
        )

    x = (
        left_x
        if column == 0
        else right_x
    )

    y = (
        legend_start_y
        + row * row_gap
    )


    # --------------------------------------------------------
    # BOLINHA
    # --------------------------------------------------------

    svg.append(
        f'<circle '
        f'cx="{x}" '
        f'cy="{y}" '
        f'r="{dot_r}" '
        f'fill="{item["color"]}"'
        f'/>'
    )


    # --------------------------------------------------------
    # TEXTO
    # --------------------------------------------------------

    language_name = shorten(
        item["name"]
    )

    label = (
        f'{escape(language_name)} '
        f'{item["pct"]:.2f}%'
    )

    svg.append(
        f'<text '
        f'x="{x + 14}" '
        f'y="{y + 5}" '
        f'fill="{text_color}" '
        f'font-family="Segoe UI, Arial, sans-serif" '
        f'font-size="14">'
        f'{label}'
        f'</text>'
    )


svg.append(
    "</svg>"
)


# ============================================================
# SALVAR
# ============================================================

OUTPUT.write_text(
    "\n".join(svg),
    encoding="utf-8",
)


print()
print("=" * 70)
print(
    f"✅ SVG GERADO: {OUTPUT}"
)
print(
    f"Dimensões: {width}x{height}"
)
print("=" * 70)