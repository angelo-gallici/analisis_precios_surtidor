import json

def exportar_geojson(df, ruta_salida):
    """
    Convierte un DataFrame en formato GeoJSON y lo guarda.

    Args:
        df (pd.DataFrame): DataFrame que debe contener columnas: latitud, longitud, empresabandera, direccion, producto, precio, fecha_vigencia
        ruta_salida (str): Ruta donde se guardará el archivo GeoJSON
    """
    features = []
    for _, row in df.iterrows():
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitud"], row["latitud"]],
            },
            "properties": {
                "bandera": row["empresabandera"],
                "direccion": row["direccion"],
                "producto": row["producto"],
                "precio": row["precio"],
                "fecha": row["fecha_vigencia"].strftime("%Y-%m-%d %H:%M:%S"),
            }
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)

    print(f"✅ GeoJSON exportado a {ruta_salida} con {len(features)} estaciones.")
