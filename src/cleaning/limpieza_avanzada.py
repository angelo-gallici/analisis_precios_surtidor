import pandas as pd
import numpy as np

def limpiar_geolocalizaciones_fuera_de_argentina(df: pd.DataFrame) -> pd.DataFrame:
    antes = len(df)
    df = df[(df["latitud"].between(-56, -21)) & (df["longitud"].between(-75, -53))]
    print(f"➤ Filtrado geográfico: {antes - len(df)} registros eliminados por estar fuera de Argentina.")
    return df

def filtrar_outliers_precio_por_producto(df: pd.DataFrame, stds: float = 3.0) -> pd.DataFrame:
    antes = len(df)
    df_limpio = pd.DataFrame()
    for prod in df["producto"].unique():
        sub = df[df["producto"] == prod].copy()
        media = sub["precio"].mean()
        std = sub["precio"].std()
        filtrado = sub[np.abs(sub["precio"] - media) <= stds * std]
        df_limpio = pd.concat([df_limpio, filtrado])
    print(f"➤ Outliers por precio: {antes - len(df_limpio)} registros eliminados como valores atípicos.")
    return df_limpio
"""
def encontrar_conflictos_de_ubicacion(df: pd.DataFrame) -> pd.DataFrame:
    conflictos = (
        df.groupby(["latitud", "longitud"])
        .agg({"empresabandera": "nunique"})
        .query("empresabandera > 1")
        .reset_index()
    )
    print(f"➤ Conflictos de ubicación: {len(conflictos)} coordenadas con más de una empresa.")
    return conflictos
"""
def limpieza_profunda(df: pd.DataFrame) -> pd.DataFrame:
    print("\n--- Limpieza avanzada ---")
    df = limpiar_geolocalizaciones_fuera_de_argentina(df)
    df = filtrar_outliers_precio_por_producto(df)
    print(f"➤ Total de registros después de limpieza avanzada: {len(df)}")
    return df
