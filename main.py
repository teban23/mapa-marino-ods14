# PROYECTO: MAPA MARINO
# ODS 14: Vida submarina

# Lista donde guardaremos los lugares registrados
import json
import html
import webbrowser
from pathlib import Path

import folium
from geopy.geocoders import Nominatim

CARPETA_DATOS = Path(__file__).parent / "datos"
CARPETA_DATOS.mkdir(exist_ok=True)

ARCHIVO = CARPETA_DATOS / "lugares.json"
ARCHIVO_MAPA = CARPETA_DATOS / "mapa_marino.html"

# Color del marcador según el tipo de lugar
ESTILOS = {
    "reciclaje": {"color": "green", "icono": "recycle"},
    "recoleccion": {"color": "orange", "icono": "trash"},
    "limpieza": {"color": "blue", "icono": "tint"},
}
ESTILO_OTRO = {"color": "gray", "icono": "map-marker"}

# Lista donde guardaremos los lugares registrados
lugares = []

geolocalizador = Nominatim(user_agent="mapa_marino_ods14")

def guardar_lugares():
    with open(ARCHIVO, "w", encoding="utf-8") as archivo:
        json.dump(lugares, archivo, indent=4, ensure_ascii=False)


def cargar_lugares():
    global lugares
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as archivo:
            lugares = json.load(archivo)
    except FileNotFoundError:
        lugares = []


# Funcion para registrar un nuevo lugar
def buscar_coordenadas(texto):
    """Intenta obtener (lat, lon) a partir de un texto. Devuelve None si falla."""
    try:
        resultado = geolocalizador.geocode(texto, timeout=10)
        if resultado:
            return resultado.latitude, resultado.longitude
    except Exception:
        pass  # Sin internet o servicio no disponible
    return None


def pedir_coordenadas_manual():
    """Pide latitud y longitud al usuario. Enter vacio = omitir."""
    print("No se encontraron coordenadas automaticamente.")
    print("Escribelas a mano (ej: 10.9685 y -74.7813) o deja vacio para omitir.")
    while True:
        lat = input("Latitud: ").strip()
        if not lat:
            return None
        lon = input("Longitud: ").strip()
        try:
            lat_f = float(lat.replace(",", "."))
            lon_f = float(lon.replace(",", "."))
            if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                return lat_f, lon_f
        except ValueError:
            pass
        print("Coordenadas no validas. Intenta nuevamente.")

def registrar_lugar():
    print("\n--- REGISTRAR NUEVO LUGAR ---")

    nombre = input("Nombre del lugar: ").strip()
    ubicacion = input("Ubicacion (barrio o ciudad): ").strip()
    tipo = input("Tipo de lugar (Reciclaje, Recoleccion o Limpieza): ").strip()
    descripcion = input("Descripcion del lugar: ").strip()

    if not nombre or not ubicacion or not tipo or not descripcion:
        print("Error: todos los campos son obligatorios.")
        return

    # Buscamos las coordenadas para poder ubicarlo en el mapa
    print("Buscando coordenadas...")
    coords = buscar_coordenadas(f"{nombre}, {ubicacion}") or buscar_coordenadas(ubicacion)
    if coords is None:
        coords = pedir_coordenadas_manual()

    # Creamos un diccionario con la informacion
    lugar = {
        "nombre": nombre,
        "ubicacion": ubicacion,
        "tipo": tipo,
        "descripcion": descripcion,
        "latitud": coords[0] if coords else None,
        "longitud": coords[1] if coords else None,
    }

    # Guardamos el lugar en la lista
    lugares.append(lugar)
    guardar_lugares()

    print("\n¡Lugar registrado correctamente!")
    if coords is None:
        print("(Sin coordenadas: no aparecera en el mapa.)")


# Funcion para mostrar todos los lugares
def mostrar_lugares():
    print("\n--- LUGARES REGISTRADOS ---")

    if len(lugares) == 0:
        print("Todavia no hay lugares registrados.")
    else:
        for numero, lugar in enumerate(lugares, start=1):
            print(f"\nLugar #{numero}")
            print(f"Nombre: {lugar['nombre']}")
            print(f"Ubicacion: {lugar['ubicacion']}")
            print(f"Tipo: {lugar['tipo']}")
            print(f"Descripcion: {lugar['descripcion']}")


# Funcion para buscar lugares por ubicacion
def buscar_lugar():
    print("\n--- BUSCAR POR UBICACION ---")

    busqueda = input("Escribe el barrio o ciudad: ").strip().lower()
    encontrados = 0

    for lugar in lugares:
        if busqueda in lugar["ubicacion"].lower():
            print(f"\nNombre: {lugar['nombre']}")
            print(f"Ubicacion: {lugar['ubicacion']}")
            print(f"Tipo: {lugar['tipo']}")
            print(f"Descripcion: {lugar['descripcion']}")
            encontrados += 1

    if encontrados == 0:
        print("No se encontraron lugares en esa ubicacion.")

def completar_coordenadas_faltantes():
    """Geolocaliza los lugares guardados que aun no tienen coordenadas."""
    cambios = False
    for lugar in lugares:
        if lugar.get("latitud") is None or lugar.get("longitud") is None:
            print(f"Buscando coordenadas de '{lugar['nombre']}'...")
            coords = buscar_coordenadas(f"{lugar['nombre']}, {lugar['ubicacion']}") \
                or buscar_coordenadas(lugar["ubicacion"])
            if coords:
                lugar["latitud"], lugar["longitud"] = coords
                cambios = True
    if cambios:
        guardar_lugares()


def generar_mapa():
    print("\n--- MAPA INTERACTIVO ---")

    if not lugares:
        print("Todavia no hay lugares registrados.")
        return

    completar_coordenadas_faltantes()

    con_coords = [
        l for l in lugares
        if l.get("latitud") is not None and l.get("longitud") is not None
    ]
    if not con_coords:
        print("Ningun lugar tiene coordenadas, no hay nada que mostrar.")
        return

    # Centro del mapa: promedio de los puntos
    lat_media = sum(l["latitud"] for l in con_coords) / len(con_coords)
    lon_media = sum(l["longitud"] for l in con_coords) / len(con_coords)

    mapa = folium.Map(location=[lat_media, lon_media], zoom_start=12, tiles=None)

    # Mapa base de calles (CARTO, funciona al abrir el HTML como archivo local)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr="&copy; OpenStreetMap contributors &copy; CARTO",
        name="Mapa de calles",
        subdomains="abcd",
        max_zoom=20,
    ).add_to(mapa)

    # Mapa base satelital
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satelite",
    ).add_to(mapa)

    # Un grupo por tipo, para activarlos/desactivarlos desde el mapa
    grupos = {}
    for lugar in con_coords:
        estilo = ESTILOS.get(lugar["tipo"].strip().lower(), ESTILO_OTRO)
        nombre_grupo = lugar["tipo"].strip().capitalize()

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

    if len(con_coords) > 1:
        mapa.fit_bounds([[l["latitud"], l["longitud"]] for l in con_coords])

    mapa.save(ARCHIVO_MAPA)
    print(f"Mapa generado con {len(con_coords)} lugar(es): {ARCHIVO_MAPA}")
    webbrowser.open(Path(ARCHIVO_MAPA).resolve().as_uri())

# Menu principal del programa
def menu():
    while True:
        print("\n==============================")
        print("         MAPA MARINO")
        print("       ODS 14: Vida submarina")
        print("==============================")
        print("1. Registrar un lugar")
        print("2. Mostrar todos los lugares")
        print("3. Buscar por ubicacion")
        print("4. Ver mapa interactivo")
        print("5. Salir")

        opcion = input("Selecciona una opcion: ")

        if opcion == "1":
            registrar_lugar()
        elif opcion == "2":
            mostrar_lugares()
        elif opcion == "3":
            buscar_lugar()
        elif opcion == "4":
            generar_mapa()
        elif opcion == "5":
            print("Gracias por ayudar a proteger nuestros oceanos.")
            break
        else:
            print("Opcion no valida. Intenta nuevamente.")


# Iniciar el programa
if __name__ == "__main__":
    cargar_lugares()
    menu()
