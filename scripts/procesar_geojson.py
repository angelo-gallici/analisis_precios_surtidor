import geopandas as gpd

# Cargar geojson original
provincias = gpd.read_file("data/raw/provincias.geojson")

# Reproyectar a sistema métrico para calcular centroides correctamente
provincias_proj = provincias.to_crs("EPSG:3857")

# Calcular centroides en proyección métrica y volver a WGS84 para guardar
provincias_proj["centroide"] = provincias_proj.geometry.centroid
provincias["centroide"] = provincias_proj["centroide"].to_crs("EPSG:4326")

# Mostrar provincias con centroide nulo
provincias_nulas = provincias[provincias["centroide"].isna()]
if not provincias_nulas.empty:
    print("Provincias con centroide nulo:")
    print(provincias_nulas[["nombre", "geometry"]])
else:
    print("Todas las provincias tienen centroides válidos.")

# Eliminar provincias con centroides nulos si hay
provincias = provincias.dropna(subset=["centroide"])

# Crear nuevo GeoDataFrame con la columna centroide como geometría
provincias_centroides = gpd.GeoDataFrame(provincias.drop(columns="geometry"), 
                                         geometry="centroide", crs="EPSG:4326")

# Guardar el GeoJSON resultante
provincias_centroides.to_file("data/processed/provincias_centroides.geojson", driver="GeoJSON")

print("GeoJSON de provincias con centroides guardado correctamente.")
