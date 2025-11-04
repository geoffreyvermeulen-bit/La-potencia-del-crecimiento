# app.py — Tot de macht van (animatie met play/pauze en pijltjes)
# ---------------------------------------------------------------
# Voer de basis a en macht b in. De animatie toont generatie voor generatie:
# - Kolom 1: a^1 stippen
# - Kolom 2: a^2 stippen (iedere stip uit kolom 1 krijgt a kinderen)
# - ...
# Bij kleine aantallen tekenen we pijltjes ouder→kind; bij grotere aantallen schakelen
# we automatisch naar een compacte weergave met duidelijke groepering.
#
# Benodigd: streamlit, matplotlib

from __future__ import annotations
import math
import time
from typing import List, Tuple

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

# ---------- Pagina & vrolijke styling ----------
st.set_page_config(page_title="Tot de macht van — animatie", page_icon="🧮", layout="centered")
st.markdown(
    """
    <style>
      .main { background: linear-gradient(180deg,#fffaf2 0%, #ffffff 75%); }
      .stApp { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
      .big { font-size: 1.5rem; font-weight: 700; }
      .note { background:#fff4c2; padding:.6rem .8rem; border-radius:.6rem; }
      .soft { color:#555; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Helpers ----------
def nice(n: int) -> str:
    if n < 1_000: return f"{n}"
    for d, name in [(10**12,"biljoen"),(10**9,"miljard"),(10**6,"miljoen"),(10**3,"duizend")]:
        if n >= d:
            v = n/d
            return (f"{v:.2f}" if v < 10 else f"{v:.1f}" if v < 100 else f"{int(round(v))}") + f" {name}"
    exp = int(math.log10(n))
    return f"{n/10**exp:.2f}e{exp}"

def positions_for_generation(a: int, g: int, x: float, tile: float) -> Tuple[list, list]:
    """
    Gen g heeft a^g punten. We tonen ze gegroepeerd per ouder:
    - aantal ouders = a^(g-1)
    - elk ouder-cluster bevat a kinderen (verticaal stapeltje)
    Plaats clusters in rijen/kolommen zodat het overzichtelijk blijft.
    """
    total = a**g
    parents = a**(g-1)
    per_parent = a

    groups_per_row = max(1, int((parents) ** 0.5))
    rows = math.ceil(parents / groups_per_row)

    xs, ys = [], []
    gap_g = 0.25 * tile      # gap tussen tegels
    gap_grp = 0.7 * tile     # gap tussen groepen
    for r in range(rows):
        for c in range(groups_per_row):
            idx_parent = r*groups_per_row + c
            if idx_parent >= parents: break
            gx = x + c * (tile + gap_grp) * per_parent
            gy = r * (tile + gap_grp) * per_parent
            # kinderen verticaal stapelen
            for k in range(per_parent):
                xs.append(gx)              # alle kinderen starten op dezelfde x binnen cluster
                ys.append(gy + k*(tile+gap_g))
    return xs, ys

# ---------- UI ----------
st.title("🧮 Tot de macht van — animatie")
st.caption("Start bij a¹. Elke stip krijgt a kinderen in de volgende kolom.")

c1, c2, c3 = st.columns([1,1,1.2])
with c1:
    a = st.number_input("Basis a", min_value=2, max_value=8, value=3, step=1)
with c2:
    b = st.number_input("Macht b (a^b)", min_value=1, max_value=10, value=5, step=1)
with c3:
    speed_ms = st.slider("Snelheid (ms per stap)", 100, 1500, 500, 50)

# Sessiestatus voor animatie
if "frame" not in st.session_state: st.session_state.frame = 1
if "playing" not in st.session_state: st.session_state.playing = False
target = int(b)

controls = st.columns([0.9,0.9,0.9,2])
with controls[0]:
    if st.button("▶️ Play"):
        st.session_state.playing = True
with controls[1]:
    if st.button("⏸️ Pause"):
        st.session_state.playing = False
with controls[2]:
    if st.button("⏮️ Reset"):
        st.session_state.playing = False
        st.session_state.frame = 1
with controls[3]:
    st.slider("Stap (kolom)", 1, target, key="frame")

st.markdown(
    f"<div class='big'>Huidig: {a}<sup>{st.session_state.frame}</sup> = "
    f"{(a**st.session_state.frame):,} <span class='soft'>({nice(a**st.session_state.frame)})</span></div>",
    unsafe_allow_html=True
)

st.markdown("<div class='note'>Tip: zet a=3 en klik Play. Je ziet: uit 1 komt 3, uit 2 komt 3, uit 3 komt 3 …</div>",
            unsafe_allow_html=True)

# ---------- Tekenen ----------
placeholder = st.empty()

def draw_until(frame: int):
    # limieten voor “vol pijltjes” vs compacte weergave
    ARROW_LIMIT_TOTAL = 220         # max pijl-objecten
    DOT_LIMIT_PER_COL = 800         # om traagheid te voorkomen

    # basismaat afhankelijk van aantal kolommen
    tile = 0.18
    x_gap = 2.2
    palette = ["#FFD166", "#06D6A0", "#EF476F", "#118AB2", "#9C6ADE", "#FF9F1C", "#2BB3FF", "#FF6F91"]

    fig_w = 2 + frame * 2.2
    fig, ax = plt.subplots(figsize=(fig_w, 6))
    ax.axis("off")
    ax.set_title("Links → rechts: iedere stip krijgt a kinderen", pad=10)

    total_arrows = 0
    # Kolom 1 t/m 'frame'
    for g in range(1, frame + 1):
        x = (g-1) * x_gap
        # bepaal posities van kinderen in deze kolom
        xs, ys = positions_for_generation(a, g, x, tile)
        # limiet per kolom
        if len(xs) > DOT_LIMIT_PER_COL:
            scale = (DOT_LIMIT_PER_COL / len(xs)) ** 0.5
            adj_tile = tile * scale
        else:
            adj_tile = tile

        # teken clusters (kleine blokjes)
        color = palette[(g-1) % len(palette)]
        for (px, py) in zip(xs, ys):
            rect = Rectangle((px, py), adj_tile, adj_tile, facecolor=color, edgecolor="white", linewidth=0.5)
            ax.add_patch(rect)

        # label boven kolom
        ax.text(x, max(ys) + adj_tile + 0.6, f"{a}^{g} = {a**g:,}".replace(",", "."),
                fontsize=10, ha="left", va="bottom")

        # pijlen van vorige kolom naar deze (alleen bij kleine aantallen)
        if g > 1:
            # posities van ouders (vorige generatie)
            pxs, pys = positions_for_generation(a, g-1, x - x_gap, tile)
            # per ouder a kinderen: verbind pijlen naar eerste 'a' kinderen van z'n cluster
            if (a**g) <= ARROW_LIMIT_TOTAL:
                for i_parent, (opx, opy) in enumerate(zip(pxs, pys)):
                    # kinderen-indexen binnen huidig xs/ys:
                    start = i_parent * a
                    end = start + a
                    if end <= len(xs):
                        for cx, cy in zip(xs[start:end], ys[start:end]):
                            arr = FancyArrowPatch((opx + adj_tile, opy + adj_tile/2),
                                                  (cx, cy + adj_tile/2),
                                                  arrowstyle="-|>", mutation_scale=8,
                                                  color="gray", alpha=0.45, linewidth=0.6)
                            ax.add_patch(arr)
                            total_arrows += 1

        # label onder kolom
        ax.text(x, -0.8, f"{g}e generatie", fontsize=10, ha="left", va="top")

    # grenzen instellen
    all_y = [0]
    for g in range(1, frame + 1):
        _, ys = positions_for_generation(a, g, (g-1)*x_gap, tile)
        if ys: all_y.append(max(ys))
    ax.set_xlim(-0.6, (frame-1)*x_gap + 2.0)
    ax.set_ylim(-1.2, max(all_y) + 3.0)

    placeholder.pyplot(fig)
    plt.close(fig)

# eerste rendering
draw_until(st.session_state.frame)

# speel af
if st.session_state.playing:
    if st.session_state.frame < target:
        time.sleep(speed_ms / 1000.0)
        st.session_state.frame += 1
        st.experimental_rerun()
    else:
        st.session_state.playing = False
