# Mapa Marino - ODS 14: Vida submarina

Aplicación en Python que permite registrar y visualizar en un mapa interactivo
los lugares de reciclaje, recolección y limpieza que ayudan a cuidar los océanos.

## Funcionalidades

- Registrar lugares con nombre, ubicación, tipo y descripción.
- Buscar lugares por barrio o ciudad.
- Obtener las coordenadas automáticamente a partir de la ubicación.
- Ver todos los lugares en un mapa interactivo con filtros por tipo.
- Usar la aplicación desde una interfaz visual en el navegador.

## Estructura del proyecto

```
ods 14/
├── main.py            # Versión de consola
├── app.py             # Interfaz visual con Streamlit
├── requirements.txt   # Librerías necesarias
└── datos/
    └── lugares.json   # Lugares registrados
```

## Instalación

1. Clona el repositorio:

```
git clone https://github.com/TU_USUARIO/mapa-marino-ods14.git
cd mapa-marino-ods14
```

2. Instala las librerías:

```
pip install -r requirements.txt
```

## Uso

Versión de consola:

```
python main.py
```

Versión con interfaz visual:

```
python -m streamlit run app.py
```

## Tecnologías

- Python
- Streamlit
- Folium
- Geopy

## Autores

- Esteban Andrés Orozco Salgado
- Sebastián Trejos Torres
- Charlis Oviedo Ardila