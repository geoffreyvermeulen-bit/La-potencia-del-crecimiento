# app.py — Tot de macht van (vrolijke, eenvoudige versie)
# --------------------------------------------------------
# Je voert a (basis) en b (macht) in. De app toont:
# - a^b met duidelijke notatie
# - per generatie (1..b) een tegel-visualisatie waarin zichtbaar is dat
#   elke "ouder" precies a "kinderen" krijgt (groeifactor = a).
# - Voor hele grote aantallen schaalt de visual automatisch.
#
# Benodigd: streamlit, matplotlib, pandas (pandas alleen voor nette weergave)

from __future__ import annotations
import math
from typing import List, Tuple

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

# ---------- Basisinstellingen & vrolijke styling ----------
st.set_page_config(page_title="Tot de macht van", page_icon="🧮", layout="centered")

# Zachte, vrolijke CSS
st.markdown(
    """
    <style>
    .main { background: linear-gradient(180deg,#fffaf2 0%, #fff 80%); }
    .stApp { font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
    .big-number { font-size: 1.6rem; font-weight: 700; }
    .muted { color: #555; }
    .note { background: #fff4c2; padding: .6rem .8rem; border-radius: .6rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Helpers ----------
SI_NAMEN = [
    (10**12, "biljoen"),
    (10**9,  "miljard"),
    (10**6,  "miljoen"),
    (10**3,  "duizend"),
]

def verkort_getal(n: int) -> str:
    if n < 0:
        return "-" + verkort_getal(-n)
    if n < 1_000:
        return f"{n}"
    for drempel, naam in SI_NAMEN:
        if n >= drempel:
            waarde = n / drempel
            if waarde < 10:
                s = f"{waarde:.2f}"
            elif waarde < 100:
                s = f"{waarde:.1f}"
            else:
                s = f"{int(round(waarde))}"
            return f"{s} {naam}"
    exp = int(math.log10(n))
    mant = n / (10**exp)
    return f"{mant:.2f}e{exp}"

def generaties_counts(a: int, b: int) -> List[int]:
    # Gen 1 = a, Gen 2 = a^2, ... Gen b = a^b
    return [a**g for g in range(1, b+1)]

def generatie_label(i: int) -> str:
    # i = 1..b
    return f"{i}e generatie"

# ---------- Hoofdkop ----------
st.title("🧮 Tot de macht van")
st.caption("Speelse kennismaking met machten — “elke tegel krijgt er a nieuwe bij”")

# ---------- Invoer ----------
col1, col2 = st.columns(2)
with col1:
    a = st.number_input("Basis a", min_value=2, max_value=12, value=3, step=1, help="Bijv. 3")
with col2:
    b = st.number_input("Macht b", min_value=1, max_value=10, value=3, step=1, help="Bijv. 3 → 3^3")

st.markdown(
    f"**Opdracht:** bereken **{a}<sup>{b}</sup>** (lees: {a} tot de macht {b}).",
    unsafe_allow_html=True
)

waarde = a**b
st.markdown(
    f"<div class='big-number'>Antwoord: {a}<sup>{b}</sup> = {waarde:,} "
    f"(<span class='muted'>{verkort_getal(waarde)}</span>)</div>",
    unsafe_allow_html=True
)

# Klein tabelletje voor overzicht
df = pd.DataFrame({
    "Generatie": [generatie_label(i) for i in range(1, b+1)],
    "Aantal": [f"{v:,}".replace(",", ".") for v in generaties_counts(a, b)],
    "Verkort": [verkort_getal(v) for v in generaties_counts(a, b)],
})
st.dataframe(df, hide_index=True, use_container_width=True)

st.markdown("---")
st.subheader("👀 Zo groeit het: elke ouder krijgt kinderen")

st.markdown(
    """
    <div class='note'>
    Bij elke stap zie je links → rechts hoe <b>iedere</b> tegel <i>precies</i> a nieuwe tegels krijgt.
    Voor grote aantallen schaalt de tekening automatisch, zodat het patroon zichtbaar blijft.
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- Visualisatie ----------
def draw_generations(a: int, b: int, max_per_col: int = 600) -> None:
    """
    Teken kolommen per generatie. Binnen een kolom groeperen we per 'ouder':
    - Gen 1: a tegels (1 groep van a)
    - Gen 2: a^2 tegels (a groepen van a)
    - Gen 3: a^3 tegels (a^2 groepen van a)
    enz.
    Om performance te bewaren tekenen we max_per_col tegels per kolom, met schaalfactor.
    """
    counts = generaties_counts(a, b)
    # Figuurbreedte schaalt mee met het aantal generaties
    fig_w = 2.1 * b
    fig, ax = plt.subplots(figsize=(fig_w, 5))

    # Tekelgrootte en marges
    x_gap = 0.9          # afstand tussen kolommen
    group_gap = 0.12     # extra ruimte tussen groepen binnen kolom
    tile_size = 0.18     # basismaat (wordt geschaald bij overschot)
    palette = ["#FFD166", "#06D6A0", "#EF476F", "#118AB2", "#9C6ADE", "#FF9F1C"]

    x = 0
    for gen_index, total in enumerate(counts, start=1):
        # Bepaal groepen in deze kolom: aantal ouders = a^(gen-1)
        parents = a**(gen_index - 1)
        children_per_parent = a

        # Schaal als er te veel tegels zijn
        scale = 1.0
        visible = total
        if total > max_per_col:
            scale = (max_per_col / total) ** 0.5  # area-schaal
            visible = max_per_col

        # Hoeveel tegels per groep (altijd = a, maar kan visueel afgeschaald worden)
        eff_tile = tile_size * scale

        # We tekenen per parent een verticaal stapeltje van 'a' tegels, met kleine gap ertussen.
        # Zet groepen in rijen/kolommen (grid) om brede kolommen te voorkomen.
        groups_per_row = max(1, int((visible / children_per_parent) ** 0.5))
        # Aantal zichtbare groepen (afgeschaald)
        vis_groups = max(1, visible // children_per_parent)

        # Bereken rijen/kolommen van groepen
        rows = math.ceil(vis_groups / groups_per_row)

        # Linksboven coördinaat van deze kolom
        col_x0 = x
        col_y0 = 0

        g_drawn = 0
        for r in range(rows):
            for c in range(groups_per_row):
                if g_drawn >= vis_groups:
                    break
                gx = col_x0 + c * (children_per_parent * eff_tile + group_gap)
                gy = col_y0 + r * (children_per_parent * eff_tile + group_gap)

                color = palette[(r * groups_per_row + c) % len(palette)]

                # Teken de 'a' kinderen als een verticaal stapeltje
                for k in range(children_per_parent):
                    # binnen 1 groep wat tussenruimte
                    tx = gx
                    ty = gy + k * (eff_tile * 1.1)
                    rect = plt.Rectangle((tx, ty), eff_tile, eff_tile, color=color, alpha=0.9)
                    ax.add_patch(rect)
                g_drawn += 1

        # Label onderaan
        ax.text(col_x0, -0.25, generatie_label(gen_index), rotation=0, va="top", ha="left", fontsize=10)

        # Volgende kolom X
        # kolombreedte = groups_per_row * (a*eff_tile + group_gap)
        col_width = max(1.2, groups_per_row * (children_per_parent * eff_tile + group_gap))
        x += col_width + x_gap

        # Bovenaan tekst “a^gen = total”
        ax.text(col_x0, gy + children_per_parent * eff_tile + 0.25,
                f"{a}^{gen_index} = {total:,}".replace(",", "."),
                fontsize=9, ha="left", va="bottom")

    # As-instellingen: we verbergen de assen voor een cleane look
    ax.set_xlim(-0.2, x)
    ax.set_ylim(-0.6, None)
    ax.axis("off")
    ax.set_title("Elke tegel krijgt er a nieuwe bij (links → rechts)", pad=12)
    st.pyplot(fig)
    plt.close(fig)

draw_generations(a, b, max_per_col=600)

# Kleine knaller voor motivatie bij “mooie” getallen
if a**b <= 1_000_000:
    st.balloons()
