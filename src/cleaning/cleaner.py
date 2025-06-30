import pandas as pd
import unicodedata
import re

def limpiar_direccion(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto)
    texto = texto.replace(",", " ")         # Evita que arruine el CSV
    texto = texto.replace("\n", " ").replace("\r", " ")  # Evita líneas rotas
    texto = re.sub(r"\s+", " ", texto)      # Normaliza espacios
    return texto.strip()


def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
    text = re.sub(r"[^\w\s]", " ", text)  # Elimina signos de puntuación
    text = re.sub(r"\s+", " ", text)      # Reemplaza múltiples espacios por uno
    return text.strip()

def simplify_word(text):
    """Normaliza y devuelve la primera palabra"""
    return normalize_text(text).split(" ")[0] if text else ""

def limpiar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "direccion" in df.columns:
        df["direccion"] = df["direccion"].apply(limpiar_direccion)


    # Eliminar columnas innecesarias
    columnas_a_eliminar = [
        "indice_tiempo", "idempresa", "cuit", "empresa",
        "region", "idtipohorario", "tipohorario","geojson"
    ]
    df.drop(columns=[col for col in columnas_a_eliminar if col in df.columns], inplace=True)

    # Normalizar texto en localidad y provincia
    df["localidad"] = df["localidad"].apply(normalize_text)
    df["provincia"] = df["provincia"].apply(normalize_text)

    # idproducto: asegurar que sea número entero
    df["idproducto"] = pd.to_numeric(df["idproducto"], errors="coerce").astype("Int64")

    # producto: eliminar paréntesis, acentos, puntos, comas, etc.
    df["producto"] = df["producto"].apply(normalize_text)

    # precio: asegurar que sea número entero
    df["precio"] = pd.to_numeric(df["precio"], errors="coerce").round().astype("Int64")

    # fecha_vigencia: parsear a datetime
    df["fecha_vigencia"] = pd.to_datetime(df["fecha_vigencia"], errors="coerce")

    # idempresabandera: asegurar enteros
    df["idempresabandera"] = pd.to_numeric(df["idempresabandera"], errors="coerce").astype("Int64")

    # empresabandera: limpiar y conservar solo primera palabra
    df["empresabandera"] = df["empresabandera"].apply(simplify_word)

        # Verificación final
    print("\n--- Verificación post-limpieza ---")
    print("Tipos de datos:")
    print(df.dtypes)

    print("\nCantidad de valores nulos por columna:")
    print(df.isnull().sum())

    # Eliminar cualquier fila que tenga un nulo
    df.dropna(inplace=True)

    print(f"\nTotal de registros después de limpieza: {len(df)}")
    print("\nCantidad de valores nulos por columna despues de la limpieza:")
    print(df.isnull().sum())


    df.reset_index(drop=True, inplace=True)
    return df

