# app.py — “A la potencia de…” (modo aula, pantalla ancha, paso a paso)
# --------------------------------------------------------------------
# Requisitos: streamlit, matplotlib

from __future__ import annotations
import math
from typing import List, Tuple

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

# ---------------- Configuración de página y estilo (pantalla completa) ----------------
st.set_page_config(page_title="A la potencia de…", page_icon="🧮", layout="wide")
st.markdown(
    """
    <style>
      /* Más espacio para el lienzo */
      .block-container {padding-top: 0.6rem; padding-bottom: 0.6rem; max-width: 2000px;}
      /* Fondo suave y tipografía amigable */
      .stApp { background: linear-gradient(180deg,#fffaf2 0%, #ffffff 70%);
               font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
      /* Ocultar menú/nota pie para clase */
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}
      .titulo {font-size: 1.6rem; font-weight: 700; margin-bottom: .2rem;}
      .sub {color:#444; margin-bottom: .6rem;}
      .barra {background:#fff4c2; padding:.6rem .8rem; border-radius:.6rem;}
      .soft {color:#555;}
      .boton-grande button {height: 3rem; font-size: 1rem;}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- Utilidades ----------------
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
            return f"{s} {nombre}"
    exp = int(math.log10(n))
    return f"{n/10**exp:.2f}e{exp}"

def subdivide_segmentos(prev_segmentos: List[Tuple[float,float]], a: int):
    """
    Divide cada segmento vertical [y0,y1] en 'a' partes iguales y
    devuelve (nuevos segmentos, centros verticales de cada subsegmento).
    Mantiene agrupados a los hijos bajo su padre.
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

def posiciones_generacion(a: int, g: int):
    """
    Calcula segmentos y centros para la generación g usando subdivisiones recursivas desde [0,1].
    """
    segmentos = [(0.0, 1.0)]
    for _ in range(g):
        segmentos, _centros = subdivide_segmentos(segmentos, a)
    # Centros de la última división
    _, centros = subdivide_segmentos([(0.0, 1.0)], 1)  # dummy para tipado
    # Recalcula centros reales para g:
    seg_tmp = [(0.0, 1.0)]
    for _ in range(g):
        seg_tmp, centros = subdivide_segmentos(seg_tmp, a)
    return seg_tmp, centros

# ---------------- Estado ----------------
if "current_gen" not in st.session_state:
    st.session_state.current_gen = 1  # comenzamos en a^1

# ---------------- Cabecera ----------------
st.markdown("<div class='titulo'>🧮 A la potencia de… — modo aula</div>", unsafe_allow_html=True)
st.markdown("<div class='sub'>Empieza en a¹. Cada paso: <b>cada punto</b> genera <b>a</b> hijos a la derecha.</div>",
            unsafe_allow_html=True)

# ---------------- Controles (solo navegación) ----------------
c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 1, 3, 8])
with c1:
    a = st.number_input("Base (a)", min_value=2, max_value=8, value=3, step=1, help="Ej.: 3")
with c2:
    b = st.number_input("Exponente (b)", min_value=1, max_value=12, value=7, step=1, help="Ej.: 7 → 3^7")
with c3:
    # Mostrar estado actual (solo texto)
    st.write(f"Gen: {st.session_state.current_gen}/{int(b)}")

with c4:
    st.markdown("<div class='barra'>Pulsa <b>Siguiente</b> para avanzar. "
                "Verás solo la(s) generación(es) más reciente(s): primero 1; "
                "luego 2; después (2 y 3), (3 y 4), etc.</div>", unsafe_allow_html=True)

# Botones grandes centrados
bc1, bc2, bc3 = st.columns([1, 1, 1])
with bc1:
    anterior = st.container()
    with anterior:
        st.markdown("<div class='boton-grande'>", unsafe_allow_html=True)
        btn_prev = st.button("⬅️ Anterior", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
with bc2:
    # Espacio
    st.write("")
with bc3:
    siguiente = st.container()
    with siguiente:
        st.markdown("<div class='boton-grande'>", unsafe_allow_html=True)
        btn_next = st.button("➡️ Siguiente", use_container_width=True, type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

# Lógica de navegación
if btn_prev:
    if st.session_state.current_gen > 1:
        st.session_state.current_gen -= 1

if btn_next:
    if st.session_state.current_gen < int(b):
        st.session_state.current_gen += 1

current = st.session_state.current_gen
objetivo = int(b)

# ---------------- Dibujo (solo 1 o 2 columnas visibles) ----------------
# Límites para mantener fluidez
LIM_FLECHAS = 320            # máximo de flechas en el paso (entre prev y actual)
LIM_PUNTOS_COL = 2500        # máximo de puntos dibujados por columna

# Preparar qué columnas mostrar:
# - Si current == 1 -> solo 1
# - Si current >= 2 -> mostrar (current-1, current)
gens_a_mostrar = [current] if current == 1 else [current - 1, current]

# Parámetros de dibujo
x_gap = 2.8                 # separación amplia para modo aula
ancho = 0.11                # ancho de bloque (rectángulo)
paleta = ["#FFD166","#06D6A0","#EF476F","#118AB2","#9C6ADE","#FF9F1C","#2BB3FF","#FF6F91"]

# Fig grande en modo ancho
fig_w = 9 if len(gens_a_mostrar) == 1 else 16
fig, ax = plt.subplots(figsize=(fig_w, 9))
ax.axis("off")
ax.set_title("Izquierda → derecha: cada punto genera a hijos", pad=10, fontsize=16)

# Para flechas, necesitamos datos de la generación anterior
segmentos_prev, ys_prev_centros = None, None

# Si mostramos dos columnas y la primera no es 1, cargamos prev explícitamente
if len(gens_a_mostrar) == 2:
    g_prev = gens_a_mostrar[0]
    seg_prev, ys_prev = posiciones_generacion(a, g_prev)
    segmentos_prev, ys_prev_centros = seg_prev, ys_prev

# Dibujo de columnas visibles
for idx, g in enumerate(gens_a_mostrar):
    x = idx * x_gap  # 0 para la primera, x_gap para la segunda
    # calcular segmentos/centros de esta generación
    seg_act, ys_centros = posiciones_generacion(a, g)
    total_puntos = a**g

    # Tamaño vertical de un subsegmento para escalar el bloque
    alto_subseg = (seg_act[0][1] - seg_act[0][0]) if seg_act else 0.05
    alto = max(0.012, alto_subseg * 0.6)

    # Muestreo si son demasiados
    muestreo = 1
    if total_puntos > LIM_PUNTOS_COL:
        muestreo = math.ceil(total_puntos / LIM_PUNTOS_COL)

    # Dibujar puntos
    color = paleta[(g-1) % len(paleta)]
    dibujados = 0
    for i, ycent in enumerate(ys_centros):
        if i % muestreo != 0:
            continue
        y0 = ycent - alto/2
        rect = Rectangle((x, y0), ancho, alto, facecolor=color, edgecolor="white", linewidth=0.6)
        ax.add_patch(rect)
        dibujados += 1

    # Etiquetas
    ax.text(x, 1.045, f"{a}^{g} = {a**g:,}".replace(",", "."),
            fontsize=13, ha="left", va="bottom")
    ax.text(x, -0.06, f"{g}ª generación", fontsize=12, ha="left", va="top")

    # Flechas solo si hay dos columnas y es la segunda (actual), y el volumen lo permite
    if len(gens_a_mostrar) == 2 and g == gens_a_mostrar[-1] and segmentos_prev is not None:
        posibles_flechas = a**(g-1) * a
        if posibles_flechas <= LIM_FLECHAS and muestreo == 1:
            for i_padre, ypad in enumerate(ys_prev_centros):
                start = i_padre * a
                for k in range(a):
                    yhijo = ys_centros[start + k]
                    arr = FancyArrowPatch((x - x_gap + ancho, ypad),
                                          (x, yhijo),
                                          arrowstyle="-|>", mutation_scale=11,
                                          color="gray", alpha=0.45, linewidth=0.9)
                    ax.add_patch(arr)
        else:
            # Nota informativa si ocultamos flechas o hay muestreo
            msg = []
            if muestreo > 1:
                msg.append("⚠️ Muestreo activo (1 de cada n).")
            if posibles_flechas > LIM_FLECHAS:
                msg.append("ℹ️ Flechas ocultas por cantidad.")
            if msg:
                ax.text(0, -0.12, "  ".join(msg), fontsize=11, ha="left", va="top", color="#555")

# Límites del lienzo
span = len(gens_a_mostrar) - 1
ax.set_xlim(-0.2, span * x_gap + 2.2)
ax.set_ylim(-0.12, 1.10)

st.pyplot(fig)
plt.close(fig)

# Pie con valor actual
st.markdown(
    f"<div class='sub'>Ahora: <b>{a}<sup>{current}</sup></b> = "
    f"<b>{(a**current):,}</b> <span class='soft'>({formatea_grande(a**current)})</span></div>",
    unsafe_allow_html=True
)
