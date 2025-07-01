import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import logging

from src.data.ingestion.api_gobierno import APIGobierno
from src.cleaning.cleaner import limpiar_dataframe
from src.cleaning.limpieza_avanzada import limpieza_profunda


# Configuración
RAW_DATA_DIR = 'data/raw/'
PROCESSED_DATA_DIR = 'data/processed/'
MASTER_FILE = os.path.join(PROCESSED_DATA_DIR, 'precios_combustibles_master.csv')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_directories():
    """Crea el directorio de datos si no existe."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

def guardar_datos_crudos(df: pd.DataFrame):
    raw_file = os.path.join(RAW_DATA_DIR, f'precios_combustibles_crudos.csv')
    df.to_csv(raw_file, index=False)
    logging.info(f"Datos crudos guardados en: {raw_file}")

def cargar_master() -> pd.DataFrame:
    """Carga el archivo maestro si existe, o crea un DataFrame vacío."""
    if os.path.exists(MASTER_FILE):
        df = pd.read_csv(MASTER_FILE, dtype=str)
        # Asegurar que fecha_vigencia sea datetime
        df['fecha_vigencia'] = pd.to_datetime(df['fecha_vigencia'], dayfirst=True, errors='coerce')
        return df
    else:
        return pd.DataFrame()

def actualizar_master(df_nuevo: pd.DataFrame, df_master: pd.DataFrame) -> pd.DataFrame:
    df_nuevo = df_nuevo.copy()
    df_nuevo['fecha_vigencia'] = pd.to_datetime(df_nuevo['fecha_vigencia'], errors='coerce')
    df_nuevo = df_nuevo.dropna(subset=['fecha_vigencia'])

    fecha_ahora = pd.Timestamp.now()

    if df_master is not None and not df_master.empty and 'fecha_vigencia' in df_master.columns:
        df_master['fecha_vigencia'] = pd.to_datetime(df_master['fecha_vigencia'], errors='coerce')
        df_master = df_master.dropna(subset=['fecha_vigencia'])
        fecha_max_master = df_master['fecha_vigencia'].max()

        # ✔ Comparar con precisión total (incluyendo hora)
        df_nuevo = df_nuevo[
            (df_nuevo['fecha_vigencia'] > fecha_max_master) &
            (df_nuevo['fecha_vigencia'] <= fecha_ahora)
        ]
    else:
        # No hay maestro: tomar todo lo que sea menor o igual a ahora
        df_nuevo = df_nuevo[df_nuevo['fecha_vigencia'] <= fecha_ahora]
        df_master = pd.DataFrame()

    if df_nuevo.empty:
        logging.info("No hay datos nuevos para agregar al archivo maestro.")
        return df_master

    df_total = pd.concat([df_master, df_nuevo], ignore_index=True)
    df_total.sort_values(by='fecha_vigencia', inplace=True)
    df_total.to_csv(MASTER_FILE, index=False)
    logging.info(f"Archivo maestro actualizado con {len(df_total)} registros.")

    fecha_min = df_total['fecha_vigencia'].min()
    fecha_max = df_total['fecha_vigencia'].max()
    print(f"\nFecha vigencia más antigua: {fecha_min}")
    print(f"Fecha vigencia más reciente: {fecha_max}")

    return df_total



def mostrar_resumen_desde_archivo():
    """Carga el archivo maestro y muestra fechas y cantidad de registros."""
    if os.path.exists(MASTER_FILE):
        df = pd.read_csv(MASTER_FILE)
        df['fecha_vigencia'] = pd.to_datetime(df['fecha_vigencia'], errors='coerce')
        fecha_min = df['fecha_vigencia'].min()
        fecha_max = df['fecha_vigencia'].max()
        print("\nResumen del archivo maestro actualizado:")
        print(f"Fecha vigencia más antigua: {fecha_min}")
        print(f"Fecha vigencia más reciente: {fecha_max}")
        print(f"Total de registros: {len(df)}")
    else:
        print("No se encontró el archivo maestro.")


def main():
    logging.info("Iniciando proceso de actualización de precios de combustibles...")
    ensure_directories()

    api = APIGobierno()

    if not api.is_online():
        logging.warning("La API del gobierno no está disponible. Abortando.")
        return

    try:
        df_original = api.get_gas_prices_dataframe()

        if df_original is not None and not df_original.empty:
            logging.info(f"Datos nuevos obtenidos: {len(df_original)} registros.")

            # Guardar versión cruda en RAW
            guardar_datos_crudos(df_original)

            # Procesamiento completo
            df_original = limpiar_dataframe(df_original)
            df_original = limpieza_profunda(df_original)

            # Actualización y guardado en PROCESSED
            df_master = cargar_master()
            actualizar_master(df_original, df_master)
            mostrar_resumen_desde_archivo()
        else:
            logging.warning("No se recibieron datos nuevos desde la API.")
            mostrar_resumen_desde_archivo()

    except Exception as e:
        logging.error(f"Error inesperado: {e}", exc_info=True)


if __name__ == "__main__":
    main()
