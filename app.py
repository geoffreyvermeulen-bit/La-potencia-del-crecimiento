# app.py
# Exponentiële groei — interactieve webapp met animatie (Streamlit)
# ---------------------------------------------------------------
# Functies:
# - Invoer met sliders/keuzes
# - Animatie per generatie (dag)
# - Tabel met exact/verkort/wetenschappelijke notatie
# - Download als CSV
# - Keuze: "alleen kinderen" (factor=k) of "ouders blijven + kinderen" (factor=k+1)
#
# Benodigd: streamlit, matplotlib, pandas

from __future__ import annotations
import math
import time
from typing import List

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================
# Hulpfuncties
# ==========================

SI_NAMEN = [
    (10**12, "biljoen"),  # Lange schaal NL: 10^12
    (10**9,  "miljard"),
    (10**6,  "miljoen"),
    (10**3,  "duizend"),
]

def verkort_getal(n: int) -> str:
    """Grote aantallen leesbaar maken (duizend/miljoen/miljard/biljoen) met fallback."""
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

def simuleer(start: int, k: int, generaties: int, inclusief_ouders: bool) -> List[int]:
    """Populatie per generatie, incl. generatie 0."""
    factor = (1 + k) if inclusief_ouders else k
    data = [start]
    for _ in range(generaties):
        data.append(data[-1] * factor)
    return data

def generatie_label(i: int) -> str:
    return f"{i}e generatie"

def maak_dataframe(pop: List[int]) -> pd.DataFrame:
    df = pd.DataFrame({
        "Generatie": list(range(len(pop))),
        "Aantal (exact)": [f"{v:,}".replace(",", ".") for v in pop],
        "Verkort": [verkort_getal(v) for v in pop],
        "Wetenschappelijk": [f"{v:.2e}" for v in pop],
        "Ruw": pop,  # handig voor sorteren/plots (onzichtbaar te maken)
    })
    return df

# ==========================
# UI
# ==========================

st.set_page_config(page_title="Exponentiële groei — Animatie", page_icon="📈", layout="centered")
st.title("📈 Exponentiële groei — animatie en generaties")
st.caption("Interactieve simulatie voor begrip van exponentiële groei (bacteriën).")

with st.expander("Didactische uitleg", expanded=False):
    st.markdown(
        """
- **Alleen kinderen tellen (factor = k)**: sluit aan bij het voorbeeld *3 → 9 → 27*.
- **Ouders blijven + kinderen (factor = k+1)**: veelgebruikte populatiemodellen waarin ouders niet verdwijnen.
- **Lineair vs. logaritmisch**: lineair laat zien hoe de grafiek ‘uit beeld schiet’; log maakt het patroon zichtbaar.
        """
    )

col1, col2 = st.columns(2)
with col1:
    start = st.number_input("Startaantal (dag 0)", min_value=1, max_value=10**12, value=3, step=1)
    k = st.number_input("Kinderen per bacterie per dag (k)", min_value=1, max_value=10**6, value=3, step=1)
    generaties = st.slider("Aantal generaties (dagen)", min_value=1, max_value=120, value=20)
with col2:
    inclusief_ouders = st.radio(
        "Tel je de ouders mee?",
        options=["Nee, alleen kinderen (factor = k)", "Ja, ouders blijven + kinderen (factor = k+1)"],
        index=0,
    ).startswith("Ja")
    schaal = st.radio("Schaal y-as", options=["Logaritmisch", "Lineair"], index=0)
    ms_per_frame = st.slider("Snelheid animatie (ms/frame)", min_value=50, max_value=2000, value=500, step=50)

toon_tabel = st.checkbox("Toon tabel met generaties en aantallen", value=True)

# ==========================
# Simulatie & tabellen
# ==========================

pop = simuleer(int(start), int(k), int(generaties), inclusief_ouders)
factor = (1 + int(k)) if inclusief_ouders else int(k)
titel = f"Exponentiële groei (start={start}, k={k}, factor=×{factor}, generaties={generaties})"

df = maak_dataframe(pop)

# Downloadknop voor CSV
csv = df.drop(columns=["Ruw"]).to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download tabel als CSV", data=csv, file_name="exponentiele_groei.csv", mime="text/csv")

if toon_tabel:
    st.dataframe(df.drop(columns=["Ruw"]), use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("Animatie")

left, right = st.columns([1,1])
with left:
    start_btn = st.button("▶️ Start animatie", type="primary")
with right:
    reset_btn = st.button("⏹️ Reset")

# Placeholder voor grafiek en overlay
plot_placeholder = st.empty()
info_placeholder = st.empty()

def plot_tot_frame(frame: int):
    """Teken lijn t/m frame (inclusief dag 0)."""
    fig, ax = plt.subplots(figsize=(9, 5))
    x = list(range(frame + 1))
    y = pop[: frame + 1]
    ax.plot(x, y, marker="o")
    ax.set_title(titel)
    ax.set_xlabel("Generatie (dag)")
    ax.set_ylabel("Aantal bacteriën")

    if schaal == "Logaritmisch":
        ax.set_yscale("log")
        ax.grid(True, which="both", linestyle="--", linewidth=0.5)
        ymin = max(1, min(y))
        ymax = max(y)
        ax.set_ylim(ymin, max(ymax, 10))
    else:
        ax.grid(True, linestyle="--", linewidth=0.5)
        ymax = max(y)
        ax.set_ylim(0, ymax * 1.1)

    plot_placeholder.pyplot(fig)
    plt.close(fig)

def update_overlay(frame: int):
    huidige = pop[frame]
    exact = f"{huidige:,}".replace(",", ".")
    verkort = verkort_getal(huidige)
    exp = f"{huidige:.2e}"
    info_placeholder.info(
        f"**{generatie_label(frame)}** — Aantal: **{exact}**  \n"
        f"Verkort: *{verkort}* &nbsp;&nbsp;|&nbsp;&nbsp; Wetenschappelijk: *{exp}*"
    )

if reset_btn:
    # Wis weergave
    plot_tot_frame(0)
    update_overlay(0)

# Toon eerste frame standaard
if not start_btn and not reset_btn and "init_once" not in st.session_state:
    plot_tot_frame(0)
    update_overlay(0)
    st.session_state["init_once"] = True

# Animatie
if start_btn:
    # Veiligheidsrem bij extreem lange animaties
    max_frames = len(pop)
    for frame in range(max_frames):
        plot_tot_frame(frame)
        update_overlay(frame)
        time.sleep(ms_per_frame / 1000.0)
