import streamlit as st
import pandas as pd
import json
import folium
from folium.features import GeoJson
from streamlit_folium import st_folium
from branca.element import Template, MacroElement

# --- Configuración general ---
st.set_page_config(page_title="Mapa de Proyectos", layout="wide")

st.markdown("""
<style>
/* Fuerza texto y fondo en el contenedor real de Streamlit */
[data-testid="stAppViewContainer"] {
  background-color: #F3F4F7 !important;
  color: #2B2B2B !important;
}

/* Fuerza color de texto en la mayoría de elementos que Streamlit renderiza */
[data-testid="stAppViewContainer"] * {
  color: #2B2B2B;
}

/* Pero respeta tus títulos verdes/naranjas */
h1, h2, h3, h4 {
  color: #345D59 !important;
}

/* Sidebar ya la manejás, pero esto evita casos raros */
section[data-testid="stSidebar"] * {
  color: #2F3A39 !important;
}

/* Evita que los links queden “invisibles” */
a, a * {
  color: #1f77b4 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Estilos (Visualizaciones + Slicers) ---
st.markdown("""
<style>
html, body, .main {
    background-color: #F3F4F7 !important;
    font-family: 'Inter', sans-serif;
    color: #4A4A4A;
}

[data-testid="stAppViewContainer"] { background-color: #F3F4F7 !important; }
.block-container { background-color: #F3F4F7 !important; padding-top: 1rem; }
[data-testid="stHeader"] { background: rgba(0,0,0,0) !important; }

/* Sidebar gradient */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #C7CFCD 0%, #E9EEED 100%) !important;
    border-right: none !important;
}
section[data-testid="stSidebar"] * { color: #2F3A39 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] h4 {
    color: #2F3A39 !important;
    font-weight: 700;
}

/* Selects in sidebar */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.65) !important;
    border-radius: 12px !important;
    border: 1px solid rgba(0,0,0,0.10) !important;
    box-shadow: 0 6px 16px rgba(0,0,0,0.08);
}
section[data-testid="stSidebar"] div[data-baseweb="select"] > div:hover {
    background: rgba(255, 255, 255, 0.78) !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] * {
    color: #2F3A39 !important;
    font-weight: 500;
}

/* Buttons */
section[data-testid="stSidebar"] div.stButton > button {
    background: rgba(255,255,255,0.75);
    border: 1px solid rgba(0,0,0,0.12);
    color: #2F3A39;
    font-weight: 650;
    border-radius: 12px;
    padding: 0.65rem 1rem;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08);
    transition: 0.2s ease;
    width: 100%;
}
section[data-testid="stSidebar"] div.stButton > button:hover {
    background: rgba(255,255,255,0.90);
    transform: translateY(-1px);
}

h1, h2, h3, h4 { color: #345D59; font-weight: 700; }

hr {
    border: 0;
    height: 2px;
    background: linear-gradient(90deg, #D24C2B, #FC9A36);
    margin: 0.8rem 0;
}

.project-card {
    background: rgba(255, 255, 255, 0.95);
    border-radius: 18px;
    border: 1px solid rgba(0,0,0,0.08);
    padding: 18px;
    box-shadow: 0 18px 35px rgba(0,0,0,0.10);
}

.map-card {
    background: rgba(255,255,255,0.95);
    border-radius: 18px;
    border: 1px solid rgba(0,0,0,0.08);
    padding: 10px;
    box-shadow: 0 18px 35px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

# --- Título principal ---
st.markdown(
    """
    <h1 style="text-align:center; color:#345D59; margin-bottom:0;">
        <b>TRABAJO EN TERRITORIO</b>
    </h1>
    <h3 style="text-align:center; color:#FC9A36; margin-top:0;">
        EQUIPO DE ENERGÍA
    </h3>
    <hr style="margin-top:10px; margin-bottom:30px;">
    """,
    unsafe_allow_html=True
)

# --- Cargar datos ---
df = pd.read_csv("20251222 Geovisor Energia.csv")

# --- Normalizar columnas ---
df["Año"] = pd.to_numeric(df["Año"], errors="coerce").astype("Int64")
df["Departamento "] = df["Departamento "].fillna("").astype(str).str.strip()
df["Municipio "] = df["Municipio "].fillna("").astype(str).str.strip()
df["Proyecto"] = df["Proyecto"].fillna("").astype(str).str.strip()
df["Lat"] = pd.to_numeric(df["Lat"], errors="coerce")
df["Long"] = pd.to_numeric(df["Long"], errors="coerce")
df["Foto"] = df["Foto"].fillna("").astype(str).str.strip()
df["Actividad "] = df["Actividad "].fillna("").astype(str).str.strip()
df["Impacto"] = df["Impacto"].fillna("").astype(str).str.strip()

# =========================
# COLORES POR PROYECTO (marca + 2 extra con alto contraste)
# =========================
BRAND_COLORS = ["#D24C2B", "#FC9A36", "#345D59", "#6B7280"]
EXTRA_COLORS = ["#4C6EF5", "#7A3E9D"]  # contraste alto
PROJECT_COLORS = BRAND_COLORS + EXTRA_COLORS

# Mapeo estable (se mantiene aunque filtres)
all_projects = sorted(df["Proyecto"].dropna().astype(str).unique().tolist())
color_map = {p: PROJECT_COLORS[i % len(PROJECT_COLORS)] for i, p in enumerate(all_projects)}

# --- Filtros en la barra lateral ---
st.sidebar.markdown(
    """
    <div style="text-align:center; margin-bottom:20px;">
        <img src="https://transforma.global/wp-content/uploads/2024/11/logo_TR_web.png"
             style="max-width:180px; width:100%; height:auto;">
    </div>
    """,
    unsafe_allow_html=True
)


st.sidebar.header("🔍 Filtros")


default_filters = {
    "año_sel": "Todos",
    "dep_sel": "Todos",
    "mun_sel": "Todos",
    "proyecto_click": "Todos",
    "map_lat": None,
    "map_lon": None,
}
for key, val in default_filters.items():
    if key not in st.session_state:
        st.session_state[key] = val

if st.sidebar.button("🧹 Borrar todos los filtros"):
    for k, v in default_filters.items():
        st.session_state[k] = v
    st.session_state["reset_view"] = True
    st.rerun()

años = ["Todos"] + sorted(df["Año"].dropna().unique().tolist())
departamentos = ["Todos"] + sorted(df["Departamento "].unique().tolist())

if st.session_state["dep_sel"] != "Todos":
    municipios = ["Todos"] + sorted(
        df.loc[df["Departamento "] == st.session_state["dep_sel"], "Municipio "].unique().tolist()
    )
else:
    municipios = ["Todos"] + sorted(df["Municipio "].unique().tolist())

if st.session_state["mun_sel"] not in municipios:
    st.session_state["mun_sel"] = "Todos"

proyectos = ["Todos"] + sorted(df["Proyecto"].unique().tolist())
if st.session_state["proyecto_click"] not in proyectos:
    st.session_state["proyecto_click"] = "Todos"

año_sel = st.sidebar.selectbox("Año:", años, key="año_sel")
dep_sel = st.sidebar.selectbox("Departamento:", departamentos, key="dep_sel")
mun_sel = st.sidebar.selectbox("Municipio:", municipios, key="mun_sel")
proyecto_click = st.sidebar.selectbox("Proyecto:", proyectos, key="proyecto_click")

# --- Aplicar filtros ---
filtered_df = df.copy()
if año_sel != "Todos":
    filtered_df = filtered_df[filtered_df["Año"] == año_sel]
if dep_sel != "Todos":
    filtered_df = filtered_df[filtered_df["Departamento "] == dep_sel]
if mun_sel != "Todos":
    filtered_df = filtered_df[filtered_df["Municipio "] == mun_sel]
if proyecto_click != "Todos":
    filtered_df = filtered_df[filtered_df["Proyecto"] == proyecto_click]

# --- Data para puntos del mapa ---
points_df = filtered_df.dropna(subset=["Lat", "Long"]).copy()

# Proyectos presentes (para leyenda)
projects_present = sorted(points_df["Proyecto"].dropna().astype(str).unique().tolist())

# --- Cargar GeoJSON (contorno departamentos) ---
with open("co.json", "r", encoding="utf-8") as f:
    geojson = json.load(f)

# --- Vista inicial del mapa ---
if st.session_state.get("reset_view", False):
    lat_centro, lon_centro, zoom = 7.5709, -74.2973, 5
    st.session_state["reset_view"] = False
elif proyecto_click != "Todos" and not filtered_df.empty:
    seleccionado = filtered_df[filtered_df["Proyecto"] == proyecto_click]
    lat_centro = float(seleccionado["Lat"].mean())
    lon_centro = float(seleccionado["Long"].mean())
    zoom = 7
else:
    lat_centro, lon_centro, zoom = 7.5709, -74.2973, 6

# --- Layout en columnas ---
col_mapa, col_info = st.columns([2.5, 1])

# =========================
# MAPA FOLIUM CON CLICK REAL
# =========================
with col_mapa:
    st.markdown('<div class="map-card">', unsafe_allow_html=True)

    m = folium.Map(
        location=[lat_centro, lon_centro],
        zoom_start=zoom,
        tiles="CartoDB positron"
    )

    # Contorno departamentos (sin relleno)
    def style_fn(_feature):
        return {
            "fillColor": "transparent",
            "color": "#B8B8B8",
            "weight": 1.2,
            "fillOpacity": 0.0
        }

    GeoJson(
        geojson,
        name="Departamentos",
        style_function=style_fn
    ).add_to(m)

    # --- Puntos con color por proyecto ---
    for _, row in points_df.iterrows():
        proj = str(row["Proyecto"])
        depto = row["Departamento "]
        muni = row["Municipio "]

        c = color_map.get(proj, "#999999")

        folium.CircleMarker(
            location=[row["Lat"], row["Long"]],
            radius=6,
            color=c,
            weight=2,
            fill=True,
            fill_color=c,
            fill_opacity=0.90,
            tooltip=f"{proj} | {depto} - {muni}",
        ).add_to(m)

    # --- Leyenda (scroll si hay muchos) ---
    legend_items = "".join([
        f"""
        <div style="display:flex; align-items:center; margin-bottom:6px;">
            <span style="
                background:{color_map[p]};
                width:12px;
                height:12px;
                border-radius:50%;
                display:inline-block;
                margin-right:8px;
                border:1px solid rgba(0,0,0,0.3);
            "></span>
            <span style="font-size:12px; color:#2B2B2B;">{p}</span>
        </div>
        """
        for p in (projects_present if projects_present else all_projects)
    ])

    legend_html = f"""
    {{% macro html(this, kwargs) %}}
    <div style="
        position: fixed;
        bottom: 25px;
        left: 25px;
        z-index: 9999;
        background: rgba(255,255,255,0.95);
        border-radius: 14px;
        padding: 12px 14px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        width: 240px;
        border: 1px solid rgba(0,0,0,0.12);
    ">
        <div style="font-weight:700; color:#345D59; margin-bottom:8px;">
            Proyectos
        </div>
        <div style="max-height:200px; overflow-y:auto; padding-right:4px;">
            {legend_items if legend_items else "<div style='font-size:12px;'>Sin proyectos</div>"}
        </div>
    </div>
    {{% endmacro %}}
    """
    macro = MacroElement()
    macro._template = Template(legend_html)
    m.get_root().add_child(macro)

    map_state = st_folium(m, height=620, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# CAPTURAR CLICK Y GUARDARLO (SIN TOCAR EL SELECTBOX)
# =========================
if map_state and map_state.get("last_object_clicked"):
    st.session_state["map_lat"] = map_state["last_object_clicked"].get("lat")
    st.session_state["map_lon"] = map_state["last_object_clicked"].get("lng")

clicked_lat = st.session_state.get("map_lat")
clicked_lon = st.session_state.get("map_lon")

# Tolerancia para comparar coordenadas (floats)
TOL = 1e-4  # ajusta a 1e-3 si tus coords vienen redondeadas

selected_rows = pd.DataFrame()
if clicked_lat is not None and clicked_lon is not None and not points_df.empty:
    selected_rows = points_df[
        (points_df["Lat"].sub(clicked_lat).abs() < TOL) &
        (points_df["Long"].sub(clicked_lon).abs() < TOL)
    ].copy()

# =========================
# PANEL DERECHO: detalle
# =========================
with col_info:
    st.markdown("### 🧭 Información de la actividad seleccionada")

    if clicked_lat is not None and clicked_lon is not None and not selected_rows.empty:
        proyectos_en_punto = sorted(set(selected_rows["Proyecto"].tolist()))
        municipios_txt = ", ".join(sorted(set(selected_rows["Municipio "].tolist())))
        deptos_txt = ", ".join(sorted(set(selected_rows["Departamento "].tolist())))
        Actividades = sorted(set(selected_rows["Actividad "].tolist()))
        Impactos = sorted(set(selected_rows["Impacto"].tolist()))

        img_candidates = selected_rows.loc[
            selected_rows["Foto"].astype(str).str.len() > 5, "Foto"
        ]
        img = img_candidates.iloc[0] if not img_candidates.empty else ""

        st.markdown(f"""
        <div class="project-card">
            <h4 style="margin-bottom:5px; color:#345D59;">🟠 <b>Selección desde el mapa</b></h4>
            <p><b>Departamento(s):</b> {deptos_txt}</p>
            <p><b>Municipio(s):</b> {municipios_txt}</p>
            <p><b>Proyecto:</b> {", ".join(proyectos_en_punto)}</p>
            <p><b>Actividades:</b> {", ".join(Actividades)}</p>
            <p><b>Impacto:</b> {", ".join(Impactos)}</p>
            {"<img src='" + img + "' width='300' style='border-radius:10px; margin-top:10px;'>" if img else ""}
        </div>
        """, unsafe_allow_html=True)

    else:
        st.info("Haz click en un punto del mapa para ver el detalle aquí.")
