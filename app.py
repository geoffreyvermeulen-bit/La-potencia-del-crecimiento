# app.py — “A la potencia de…” (pantalla ancha, paso a paso, usando el ancho)
# ----------------------------------------------------------------------------
# Requisitos: streamlit, matplotlib

from __future__ import annotations
import math
from typing import List, Tuple

import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
from matplotlib.patches import Circle

# ---------------- Configuración de página y estilo (pantalla completa) ----------------
st.set_page_config(page_title="A la potencia de…", page_icon="🧮", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top: 0.5rem; padding-bottom: 0.5rem; max-width: 2200px;}
      .stApp { background: linear-gradient(180deg,#fffaf2 0%, #ffffff 70%);
               font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }
      #MainMenu, header, footer {visibility: hidden;}
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
def format_grande(n: int) -> str:
    """Notación corta en español: mil, millón, mil millones, billón (10^12)."""
    if n < 0:
        return "-" + format_grande(-n)
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

def layout_columna_horizontal(
    a: int,
    g: int,
    target_filas: int = 6,
    gap_item: float = 0.012,
    gap_grupo_x: float = 0.05,
    gap_grupo_y: float = 0.06,
):
    """
    Calcula la distribución de a^g 'hijos' en la columna g de forma HORIZONTAL:
      - Cada 'padre' genera un grupo de 'a' hijos colocados en una FILA (uno al lado del otro).
      - Los grupos de padres se distribuyen en 'target_filas' filas para usar la anchura.
    Devuelve:
      - child_centers_by_parent: lista de listas [(x,y) de cada hijo] para cada padre (long a).
      - item_centers: lista plana de todos los hijos (a^g).
      - medidas (tile_w, tile_h, ancho_total, alto_total, filas, grupos_por_fila).
    """
    total = a**g
    padres = a**(g-1)  # nº de grupos (uno por padre)
    grupos_por_fila = max(1, math.ceil(padres / target_filas))
    filas = math.ceil(padres / grupos_por_fila)

    # Altura disponible ~1.0; definimos alto por fila y tamaño del "tile" en función de filas
    alto_por_fila = (1.0 - (filas - 1) * gap_grupo_y) / max(1, filas)
    tile_h = max(0.012, alto_por_fila * 0.55)  # algo de margen superior/inferior
    tile_w = tile_h  # cuadrados por defecto

    # Ancho de un grupo (a hijos en fila)
    ancho_grupo = a * tile_w + (a - 1) * gap_item
    ancho_total = grupos_por_fila * ancho_grupo + (grupos_por_fila - 1) * gap_grupo_x
    alto_total = filas * tile_h + (filas - 1) * gap_grupo_y

    child_centers_by_parent = []
    item_centers = []

    for idx_padre in range(padres):
        fila = idx_padre // grupos_por_fila
        col  = idx_padre % grupos_por_fila

        gx0 = col * (ancho_grupo + gap_grupo_x)            # x de inicio del grupo
        gy0 = fila * (tile_h + gap_grupo_y)                # y de la fila

        centros_hijos = []
        for k in range(a):
            cx = gx0 + k * (tile_w + gap_item) + tile_w / 2
            cy = gy0 + tile_h / 2
            centros_hijos.append((cx, cy))
            item_centers.append((cx, cy))

        child_centers_by_parent.append(centros_hijos)

    return child_centers_by_parent, item_centers, (tile_w, tile_h, ancho_total, alto_total, filas, grupos_por_fila)

# ---------------- Estado ----------------
if "current_gen" not in st.session_state:
    st.session_state.current_gen = 1  # empezamos en a^1

# ---------------- Cabecera ----------------
st.markdown("<div class='titulo'>🧮 A la potencia de… — modo aula</div>", unsafe_allow_html=True)
st.markdown("<div class='sub'>Empieza en a¹. En cada paso, <b>cada punto</b> genera <b>a</b> hijos a la derecha.</div>",
            unsafe_allow_html=True)

# ---------------- Controles (en un mismo panel con el lienzo) ----------------
c1, c2, c3, c4, c5 = st.columns([1.3, 1.3, 1.6, 1, 6])
with c1:
    a = st.number_input("Base (a)", min_value=2, max_value=10, value=3, step=1, help="Ej.: 3")
with c2:
    b = st.number_input("Exponente (b)", min_value=1, max_value=12, value=7, step=1, help="Ej.: 7 → 3^7")
with c3:
    estilo = st.radio("Estilo", ["Bloques", "Bolitas"], horizontal=True, index=0)
with c4:
    st.write(f"Gen: {st.session_state.current_gen}/{int(b)}")
with c5:
    st.markdown("<div class='barra'>Pulsa <b>Siguiente</b> para avanzar. "
                "Se muestran solo las últimas generaciones: primero 1; luego 2; después (2 y 3), (3 y 4), etc.</div>",
                unsafe_allow_html=True)

bc1, bc2, bc3 = st.columns([1, 1, 1])
with bc1:
    st.markdown("<div class='boton-grande'>", unsafe_allow_html=True)
    btn_prev = st.button("⬅️ Anterior", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
with bc2:
    st.write("")
with bc3:
    st.markdown("<div class='boton-grande'>", unsafe_allow_html=True)
    btn_next = st.button("➡️ Siguiente", use_container_width=True, type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

# Navegación
if btn_prev and st.session_state.current_gen > 1:
    st.session_state.current_gen -= 1
if btn_next and st.session_state.current_gen < int(b):
    st.session_state.current_gen += 1

current = st.session_state.current_gen
objetivo = int(b)

# ---------------- Parámetros de dibujo ----------------
# Límites para mantener fluidez
ARROW_LIMIT = 350          # máximo de flechas entre 2 columnas
ITEM_LIMIT  = 6000         # máximo de elementos dibujados por columna antes de aplicar muestreo
ROWS_TARGET = 6            # cuántas filas de grupos intentamos usar (aprovecha el ancho)

x_gap_cols = 1.2           # separación entre columna anterior y actual
paleta = ["#FFD166","#06D6A0","#EF476F","#118AB2","#9C6ADE","#FF9F1C","#2BB3FF","#FF6F91"]

# ---------------- Determinar qué columnas mostrar ----------------
gens_visibles = [current] if current == 1 else [current - 1, current]

# Precalcular layouts
layouts = {}
total_width_units = 0.0
for i, g in enumerate(gens_visibles):
    child_by_parent, items, (tile_w, tile_h, ancho_total, alto_total, filas, gpf) = layout_columna_horizontal(
        a=a, g=g, target_filas=ROWS_TARGET
    )
    layouts[g] = {
        "child_by_parent": child_by_parent,
        "items": items,
        "tile_w": tile_w,
        "tile_h": tile_h,
        "ancho_total": ancho_total,
        "alto_total": alto_total,
    }
    total_width_units += ancho_total
total_width_units += x_gap_cols * (len(gens_visibles) - 1)

# ---------------- Lienzo grande ----------------
fig_w = 18 if len(gens_visibles) == 2 else 12  # bastante ancho
fig_h = 9
fig, ax = plt.subplots(figsize=(fig_w, fig_h))
ax.axis("off")
ax.set_title("De izquierda a derecha: cada punto genera a hijos", pad=14, fontsize=16)

# Dibujo de columnas
x_offset = 0.0
prev_g = None
for idx, g in enumerate(gens_visibles):
    L = layouts[g]
    tile_w = L["tile_w"]
    tile_h = L["tile_h"]
    ancho_total = L["ancho_total"]
    alto_total = L["alto_total"]
    child_by_parent = L["child_by_parent"]

    # Dibuja elementos de la columna g
    color = paleta[(g-1) % len(paleta)]
    total_items = a**g
    muestreo = 1
    if total_items > ITEM_LIMIT:
        muestreo = math.ceil(total_items / ITEM_LIMIT)

    # Dibujar puntos (bloques o bolitas)
    dibujados = 0
    for p_idx, hijos in enumerate(child_by_parent):
        for k, (cx, cy) in enumerate(hijos):
            # muestreo global por índice absoluto
            abs_index = p_idx * a + k
            if abs_index % muestreo != 0:
                continue
            if estilo == "Bloques":
                rect = Rectangle((x_offset + cx - tile_w/2, cy - tile_h/2),
                                 tile_w, tile_h, facecolor=color, edgecolor="white", linewidth=0.6)
                ax.add_patch(rect)
            else:  # Bolitas
                circ = Circle((x_offset + cx, cy), radius=min(tile_w, tile_h)/2,
                              facecolor=color, edgecolor="white", linewidth=0.6)
                ax.add_patch(circ)
            dibujados += 1

    # Etiquetas superior e inferior
    ax.text(x_offset, 1.05, f"{a}^{g} = {a**g:,}".replace(",", "."),
            fontsize=13, ha="left", va="bottom")
    ax.text(x_offset, -0.08, f"{g}ª generación",
            fontsize=12, ha="left", va="top")

    # Flechas desde la columna anterior hacia ésta (solo si hay 2 columnas)
    if prev_g is not None:
        # posibles flechas = a^(g-1) * a ; si es razonable y sin muestreo, dibujamos
        posibles = a**(g-1) * a
        if posibles <= ARROW_LIMIT and muestreo == 1:
            prev_items = layouts[prev_g]["items"]  # centros de los padres (todos los puntos de la gen anterior)
            for i_padre, padre_center in enumerate(prev_items):
                px, py = padre_center
                for (cx, cy) in child_by_parent[i_padre]:
                    arr = FancyArrowPatch((x_offset - x_gap_cols + px + tile_w/2, py),
                                          (x_offset + cx - tile_w/2, cy),
                                          arrowstyle="-|>", mutation_scale=12,
                                          color="gray", alpha=0.45, linewidth=1.0)
                    ax.add_patch(arr)
        else:
            msg = []
            if muestreo > 1:
                msg.append("⚠️ Muestreo activo (se muestra 1 de cada n).")
            if posibles > ARROW_LIMIT:
                msg.append("ℹ️ Flechas ocultas por cantidad.")
            if msg:
                ax.text(x_offset - 0.2, -0.12, "  ".join(msg), fontsize=11, ha="left", va="top", color="#555")

    # Avanza offset horizontal para la próxima columna visible
    x_offset += ancho_total + x_gap_cols
    prev_g = g

# Límites y renderizado
span = len(gens_visibles)
ax.set_xlim(-0.2, total_width_units + 0.2)
ax.set_ylim(-0.12, 1.10)

st.pyplot(fig, use_container_width=True)
plt.close(fig)

# Pie con valor actual (visible y grande)
st.markdown(
    f"<div class='sub'>Ahora: <b>{a}<sup>{current}</sup></b> = "
    f"<b>{(a**current):,}</b> <span class='soft'>({format_grande(a**current)})</span></div>",
    unsafe_allow_html=True
)
