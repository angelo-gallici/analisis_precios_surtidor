# src/cleaning/rules.py

reglas_basicas = [
    {
        "tipo": "renombrar_columnas",
        "mapeo": {
            "empresa": "nombre_empresa",
            "producto": "tipo_combustible",
            "provincia": "provincia",
            "precio": "precio"
        }
    },
    {
        "tipo": "normalizar_string",
        "columnas": ["nombre_empresa", "tipo_combustible", "provincia"]
    },
    {
        "tipo": "formato_fecha",
        "columna": "fecha_vigencia"
    },
    {
        "tipo": "eliminar_columnas",
        "columnas": ["geojson", "indice_tiempo"]
    }
]
