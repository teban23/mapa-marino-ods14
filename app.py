import html
import json
from pathlib import Path

import folium
import streamlit as st
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

# Usa el mismo lugares.json que main.py (deben estar en la misma carpeta)
CARPETA_DATOS = Path(__file__).parent / "datos"
CARPETA_DATOS.mkdir(exist_ok=True)
ARCHIVO = CARPETA_DATOS / "lugares.json"

TIPOS = ["Reciclaje", "Recoleccion", "Limpieza"]
ESTILOS = {
    "reciclaje": {"color": "green", "icono": "recycle"},
    "recoleccion": {"color": "orange", "icono": "trash"},
    "limpieza": {"color": "blue", "icono": "tint"},
}
ESTILO_OTRO = {"color": "gray", "icono": "map-marker"}

st.set_page_config(page_title="Mapa Marino - ODS 14", page_icon="🌊", layout="wide")


# ---------- Datos ----------
def cargar():
    if ARCHIVO.exists():
        return json.loads(ARCHIVO.read_text(encoding="utf-8"))
    return []


def guardar(lugares):
    ARCHIVO.write_text(
        json.dumps(lugares, indent=4, ensure_ascii=False), encoding="utf-8"
    )


@st.cache_resource
def obtener_geolocalizador():
    return Nominatim(user_agent="mapa_marino_ods14")


def buscar_coordenadas(texto):
    """Devuelve (lat, lon) o None si no se encuentra o no hay internet."""
    try:
        resultado = obtener_geolocalizador().geocode(texto, timeout=10)
        if resultado:
            return resultado.latitude, resultado.longitude
    except Exception:
        pass
    return None


def tiene_coords(lugar):
    return lugar.get("latitud") is not None and lugar.get("longitud") is not None


# ---------- Mapa ----------
def construir_mapa(lugares):
    lat_media = sum(l["latitud"] for l in lugares) / len(lugares)
    lon_media = sum(l["longitud"] for l in lugares) / len(lugares)

    mapa = folium.Map(location=[lat_media, lon_media], zoom_start=13, tiles=None)

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr="&copy; OpenStreetMap contributors &copy; CARTO",
        name="Mapa de calles",
        subdomains="abcd",
        max_zoom=20,
    ).add_to(mapa)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satelite",
    ).add_to(mapa)

    grupos = {}
    for lugar in lugares:
        nombre_grupo = lugar["tipo"].strip().capitalize()
        estilo = ESTILOS.get(lugar["tipo"].strip().lower(), ESTILO_OTRO)

        if nombre_grupo not in grupos:
            grupos[nombre_grupo] = folium.FeatureGroup(name=nombre_grupo).add_to(mapa)

        popup_html = (
            f"<b>{html.escape(lugar['nombre'])}</b><br>"
            f"<i>{html.escape(lugar['tipo'])}</i><br>"
            f"{html.escape(lugar['ubicacion'])}<br><br>"
            f"{html.escape(lugar['descripcion'])}"
        )
        folium.Marker(
            location=[lugar["latitud"], lugar["longitud"]],
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=lugar["nombre"],
            icon=folium.Icon(color=estilo["color"], icon=estilo["icono"], prefix="fa"),
        ).add_to(grupos[nombre_grupo])

    folium.LayerControl(collapsed=False).add_to(mapa)

    if len(lugares) > 1:
        mapa.fit_bounds([[l["latitud"], l["longitud"]] for l in lugares])
    return mapa


def pagina_mapa(lugares):
    st.header("🗺️ Mapa interactivo")

    con_coords = [l for l in lugares if tiene_coords(l)]
    sin_coords = len(lugares) - len(con_coords)

    col1, col2 = st.columns(2)
    col1.metric("Lugares registrados", len(lugares))
    col2.metric("Lugares en el mapa", len(con_coords))

    if sin_coords:
        st.warning(f"{sin_coords} lugar(es) no tienen coordenadas y no se muestran.")
        if st.button("Buscar coordenadas faltantes"):
            with st.spinner("Buscando coordenadas..."):
                for lugar in lugares:
                    if not tiene_coords(lugar):
                        coords = buscar_coordenadas(
                            f"{lugar['nombre']}, {lugar['ubicacion']}"
                        ) or buscar_coordenadas(lugar["ubicacion"])
                        if coords:
                            lugar["latitud"], lugar["longitud"] = coords
                guardar(lugares)
            st.rerun()

    if not con_coords:
        st.info("Todavía no hay lugares con coordenadas. Registra uno en el menú de la izquierda.")
        return

    tipos_disponibles = sorted({l["tipo"].strip().capitalize() for l in con_coords})
    elegidos = st.multiselect("Filtrar por tipo", tipos_disponibles, default=tipos_disponibles)
    visibles = [l for l in con_coords if l["tipo"].strip().capitalize() in elegidos]

    if not visibles:
        st.info("Selecciona al menos un tipo para ver el mapa.")
        return

    st_folium(construir_mapa(visibles), height=550, use_container_width=True, returned_objects=[])


# ---------- Registrar ----------
def pagina_registrar(lugares):
    st.header("➕ Registrar un lugar")

    with st.form("formulario_registro", clear_on_submit=True):
        nombre = st.text_input("Nombre del lugar")
        ubicacion = st.text_input("Ubicación (barrio o ciudad)")
        tipo = st.selectbox("Tipo de lugar", TIPOS)
        descripcion = st.text_area("Descripción del lugar")

        with st.expander("¿Conoces las coordenadas? (opcional)"):
            st.caption("Si las dejas vacías, se buscarán automáticamente. Ejemplo: 10.9685 y -74.7813")
            lat_txt = st.text_input("Latitud")
            lon_txt = st.text_input("Longitud")

        enviar = st.form_submit_button("Registrar lugar")

    if not enviar:
        return

    nombre, ubicacion, descripcion = nombre.strip(), ubicacion.strip(), descripcion.strip()
    if not nombre or not ubicacion or not descripcion:
        st.error("Todos los campos son obligatorios.")
        return

    coords = None
    if lat_txt.strip() and lon_txt.strip():
        try:
            lat = float(lat_txt.replace(",", "."))
            lon = float(lon_txt.replace(",", "."))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                coords = (lat, lon)
            else:
                st.error("Las coordenadas están fuera de rango.")
                return
        except ValueError:
            st.error("Las coordenadas deben ser números.")
            return
    else:
        with st.spinner("Buscando coordenadas..."):
            coords = buscar_coordenadas(f"{nombre}, {ubicacion}") or buscar_coordenadas(ubicacion)

    lugares.append(
        {
            "nombre": nombre,
            "ubicacion": ubicacion,
            "tipo": tipo,
            "descripcion": descripcion,
            "latitud": coords[0] if coords else None,
            "longitud": coords[1] if coords else None,
        }
    )
    guardar(lugares)

    st.success("¡Lugar registrado correctamente!")
    if coords is None:
        st.warning("No se encontraron coordenadas, así que no aparecerá en el mapa por ahora.")


# ---------- Lista y búsqueda ----------
def pagina_lista(lugares):
    st.header("📋 Lugares registrados")

    if not lugares:
        st.info("Todavía no hay lugares registrados.")
        return

    busqueda = st.text_input("Buscar por barrio o ciudad").strip().lower()
    filtrados = [l for l in lugares if busqueda in l["ubicacion"].lower()]

    if not filtrados:
        st.info("No se encontraron lugares en esa ubicación.")
        return

    st.dataframe(
        [
            {
                "Nombre": l["nombre"],
                "Ubicación": l["ubicacion"],
                "Tipo": l["tipo"],
                "Descripción": l["descripcion"],
            }
            for l in filtrados
        ],
        use_container_width=True,
        hide_index=True,
    )


# ---------- Programa principal ----------
st.sidebar.title("🌊 Mapa Marino")
st.sidebar.caption("ODS 14: Vida submarina")
seccion = st.sidebar.radio("Menú", ["Mapa", "Registrar un lugar", "Lista y búsqueda"])

lugares = cargar()

if seccion == "Mapa":
    pagina_mapa(lugares)
elif seccion == "Registrar un lugar":
    pagina_registrar(lugares)
else:
    pagina_lista(lugares)