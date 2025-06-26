# src/cleaning/helpers.py

import pandas as pd

def aplicar_regla(df: pd.DataFrame, regla: dict) -> pd.DataFrame:
    tipo = regla.get("tipo")

    if tipo == "renombrar_columnas":
        return df.rename(columns=regla["mapeo"])

    if tipo == "normalizar_string":
        for col in regla["columnas"]:
            df[col] = df[col].astype(str).str.strip().str.upper()
        return df

    if tipo == "formato_fecha":
        col = regla["columna"]
        df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    if tipo == "eliminar_columnas":
        return df.drop(columns=regla["columnas"], errors="ignore")

    return df
