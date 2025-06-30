import pandas as pd
from datetime import datetime

def detectar_ultima_variacion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.sort_values(by=["latitud", "longitud", "idproducto", "fecha_vigencia"], inplace=True)

    resultados = []

    for (lat, lon, idprod), grupo in df.groupby(["latitud", "longitud", "idproducto"]):
        grupo = grupo.sort_values("fecha_vigencia")
        precios = grupo["precio"].values
        fechas = grupo["fecha_vigencia"].values

        precio_actual = precios[-1]
        fecha_actual = fechas[-1]

        # Buscar última variación real (de atrás hacia adelante)
        for i in range(len(precios) - 2, -1, -1):
            if precios[i] != precio_actual:
                precio_anterior = precios[i]
                fecha_cambio = fechas[i + 1]  # Donde ocurrió el cambio
                diferencia = precio_actual - precio_anterior

                if diferencia > 0:
                    variacion = "subio"
                elif diferencia < 0:
                    variacion = "bajo"
                else:
                    variacion = "sin cambio"  # No debería pasar

                dias = (fecha_actual - fecha_cambio).days

                resultados.append({
                    "latitud": lat,
                    "longitud": lon,
                    "idproducto": idprod,
                    "precio_anterior": precio_anterior,
                    "precio_actual": precio_actual,
                    "fecha_ultimo_cambio": fecha_cambio,
                    "variacion": variacion,
                    "dias_desde_ultima_variacion": dias,
                })
                break
        else:
            # Nunca hubo cambio, conservar solo el valor actual
            resultados.append({
                "latitud": lat,
                "longitud": lon,
                "idproducto": idprod,
                "precio_anterior": None,
                "precio_actual": precio_actual,
                "fecha_ultimo_cambio": None,
                "variacion": "sin datos previos",
                "dias_desde_ultima_variacion": None,
            })

    return pd.DataFrame(resultados)
