# app.py — “A la potencia de…” (animación clara para primaria, en español)
# ------------------------------------------------------------------------
# Qué hace:
# - Introduce base (a) y exponente (b).
# - Muestra a^1, a^2, … con una animación Play/Pausa/Reset.
# - Cada punto (padre) genera a hijos en la siguiente columna.
# - Con pocos puntos: flechas padre→hijos. Con muchos: muestreo y aviso.
# - Todo en español. Números grandes en formato legible.
#
# Requisitos: streamlit, matplotlib

from __future__ import annotations
import math
import time
from typing import List, Tuple

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

# -------------- Configuración de página y estilo --------------
st.set_page_config(page_title="A la potencia de…", page_icon="🧮", layout="centered")
st.markdown(
    """
    <style>
      .main { background: linear-gradient(180deg,#fffaf2 0%, #ffffff 75%); }
      .stApp { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
      .big  { font-size: 1.4rem; font-weight: 700; }
      .note { background:#fff4c2; padding:.6rem .8rem; border-radius:.6rem; }
      .soft { color:#555; }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------- Utilidades --------------
def formatea_grande(n: int) -> str:
    """Notación corta en español: mil, millón, mil millones, billón (10^12)."""
    if n < 0:
        return "-" + formatea_grande(-n)
    if n < 1_000:
        return f"{n}"
    for d, nombre in [(10**12,"billón"), (10**9,"mil millones"), (10**6,"millón"), (10**3,"mil")]:
        if n >= d:
            v = n / d
            if v < 10:   s = f"{v:.2f}"
            elif v < 100: s = f"{v:.1f}"
            else:         s = f"{int(round(v))}"
            # singular/plural sencillo
            suf = nombre if s == "1" else nombre
            return f"{s} {suf}"
    exp = int(math.log10(n))
    return f"{n/10**exp:.2f}e{exp}"

def subdivide_segmentos(prev_segmentos: List[Tuple[float,float]], a: int):
    """
    Recibe una lista de segmentos verticales [y0,y1].
    Devuelve:
      - nuevos segmentos (cada uno subdividido en 'a' partes),
      - y posiciones y-centro (una por hijo).
    Así los hijos quedan agrupados bajo su padre.
    """
    nuevos = []
    ys_centros = []
    for (y0, y1) in prev_segmentos:
        h = (y1 - y0) / a
        for j in range(a):
            c0 = y0 + j*h
            c1 = c0 + h
            nuevos.append((c0, c1))
            ys_centros.append((c0 + c1) / 2.0)
    return nuevos, ys_centros

# -------------- Cabecera e inputs --------------
st.title("🧮 A la potencia de… — animación paso a paso")
st.caption("Comienza en a¹. En cada paso, **cada punto** genera **a** hijos en la columna siguiente.")

c1, c2, c3 = st.columns([1,1,1.2])
with c1:
    a = st.number_input("Base (a)", min_value=2, max_value=8, value=3, step=1, help="Ej.: 3")
with c2:
    b = st.number_input("Exponente (b)", min_value=1, max_value=10, value=5, step=1, help="Ej.: 5 → 3^5")
with c3:
    speed_ms = st.slider("Velocidad (ms por paso)", 100, 1500, 500, 50)

# Estado seguro (claves separadas para evitar el error con widgets)
if "anim_frame" not in st.session_state:
    st.session_state.anim_frame = 1
if "slider_frame" not in st.session_state:
    st.session_state.slider_frame = 1
if "playing" not in st.session_state:
    st.session_state.playing = False

objetivo = int(b)

def sync_desde_slider():
    # Cuando el usuario mueve el slider, sincronizamos el fotograma de animación
    st.session_state.anim_frame = st.session_state.slider_frame

# Controles
controles = st.columns([0.9,0.9,0.9,2])
with controles[0]:
    if st.button("▶️ Reproducir"):
        st.session_state.playing = True
with controles[1]:
    if st.button("⏸️ Pausa"):
        st.session_state.playing = False
with controles[2]:
    if st.button("⏮️ Reiniciar"):
        st.session_state.playing = False
        st.session_state.anim_frame = 1
        st.session_state.slider_frame = 1
with controles[3]:
    st.slider("Paso (columna)", 1, objetivo, key="slider_frame", on_change=sync_desde_slider)

# Encabezado de estado actual
actual = st.session_state.anim_frame
st.markdown(
    f"<div class='big'>Ahora: {a}<sup>{actual}</sup> = "
    f"{(a**actual):,} <span class='soft'>({formatea_grande(a**actual)})</span></div>",
    unsafe_allow_html=True
)
st.markdown(
    "<div class='note'>Sugerencia: pon a=3 y pulsa Reproducir. Verás: del 1 sale 3, del 2 sale 3, del 3 sale 3…</div>",
    unsafe_allow_html=True
)

# -------------- Dibujo --------------
placeholder = st.empty()

def dibuja_hasta(frame: int):
    """
    Dibuja columnas desde a^1 hasta a^frame.
    Para cada columna g:
      - coloco a^g puntos (hijos) dentro de subsegmentos del intervalo [0,1].
      - si el total es pequeño, dibujo flechas desde cada padre (columna g-1) a sus 'a' hijos.
    """
    # Límites para mantener fluidez
    LIM_FLECHAS = 280               # máximo de flechas en un paso
    LIM_PUNTOS_COL = 2500           # máximo de puntos dibujados en una columna
    usar_flechas = True

    # Geometría
    x_gap = 1.6                      # separación horizontal entre columnas
    ancho = 0.075                    # ancho de cada punto (rectángulo)
    paleta = ["#FFD166","#06D6A0","#EF476F","#118AB2","#9C6ADE","#FF9F1C","#2BB3FF","#FF6F91"]

    fig_w = 2 + frame * 1.9
    fig, ax = plt.subplots(figsize=(fig_w, 6))
    ax.axis("off")
    ax.set_title("Izquierda → derecha: cada punto genera a hijos", pad=10)

    # Segmentos del paso anterior (inicialmente un segmento total)
    segmentos_prev = [(0.0, 1.0)]
    ys_prev_centros = [0.5]  # centro del segmento inicial (conceptual)

    for g in range(1, frame + 1):
        x = (g-1) * x_gap

        # Subdividir cada segmento del paso anterior en 'a' segmentos nuevos (uno por hijo)
        segmentos_act, ys_centros = subdivide_segmentos(segmentos_prev, a)

        total_puntos = a**g

        # Altura del punto: una fracción del tamaño del subsegmento (para no tocar bordes)
        alto_subseg = (segmentos_act[0][1] - segmentos_act[0][0]) if segmentos_act else 0.05
        alto = max(0.008, alto_subseg * 0.6)

        # ¿Hay que muestrear?
        muestreo = 1
        if total_puntos > LIM_PUNTOS_COL:
            muestreo = math.ceil(total_puntos / LIM_PUNTOS_COL)

        # Dibujar puntos de esta columna
        color = paleta[(g-1) % len(paleta)]
        cont_dib = 0
        for idx, ycent in enumerate(ys_centros):
            if idx % muestreo != 0:
                continue
            y0 = ycent - alto/2
            rect = Rectangle((x, y0), ancho, alto, facecolor=color, edgecolor="white", linewidth=0.5)
            ax.add_patch(rect)
            cont_dib += 1

        # Etiquetas
        ax.text(x, 1.04, f"{a}^{g} = {a**g:,}".replace(",", "."),
                fontsize=10, ha="left", va="bottom")
        ax.text(x, -0.06, f"{g}ª generación", fontsize=10, ha="left", va="top")

        # Flechas desde padres → hijos (solo si es razonable)
        if g > 1:
            posibles_flechas = a**(g-1) * a
            if posibles_flechas <= LIM_FLECHAS and muestreo == 1:
                for i_padre, ypad in enumerate(ys_prev_centros):
                    # hijos del padre i: son 'a' segmentos consecutivos
                    start = i_padre * a
                    for k in range(a):
                        h_idx = start + k
                        yhijo = ys_centros[h_idx]
                        arr = FancyArrowPatch((x - x_gap + ancho, ypad),
                                              (x, yhijo),
                                              arrowstyle="-|>", mutation_scale=9,
                                              color="gray", alpha=0.5, linewidth=0.7)
                        ax.add_patch(arr)
            else:
                usar_flechas = False

        # Preparar para el siguiente paso
        segmentos_prev = segmentos_act
        ys_prev_centros = ys_centros

    # Límites del gráfico
    ax.set_xlim(-0.2, (frame-1)*x_gap + 2.0)
    ax.set_ylim(-0.12, 1.10)

    # Notas informativas si hay muestreo o si ocultamos flechas
    notas = []
    if any((a**g) > LIM_PUNTOS_COL for g in range(1, frame+1)):
        notas.append("⚠️ Muestreo activo en columnas con muchos puntos (se muestra 1 de cada *n*).")
    if not usar_flechas:
        notas.append("ℹ️ Flechas ocultas automáticamente cuando hay demasiadas.")

    if notas:
        ax.text(0, -0.12, "  ".join(notas), fontsize=9, ha="left", va="top", color="#555")

    placeholder.pyplot(fig)
    plt.close(fig)

# Primera representación
dibuja_hasta(st.session_state.anim_frame)

# Reproducir
if st.session_state.playing:
    if st.session_state.anim_frame < objetivo:
        time.sleep(speed_ms / 1000.0)
        st.session_state.anim_frame += 1
        # mantener slider sincronizado:
        st.session_state.slider_frame = st.session_state.anim_frame
        st.experimental_rerun()
    else:
        st.session_state.playing = False
