import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import logging

from src.data.ingestion.api_gobierno import APIGobierno

# Configuración
RAW_DATA_DIR = 'data/raw/'
MASTER_FILE = os.path.join(RAW_DATA_DIR, 'precios_combustibles_master.csv')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ensure_directories():
    """Crea el directorio de datos si no existe."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)

def cargar_master() -> pd.DataFrame:
    """Carga el archivo maestro si existe, o crea un DataFrame vacío."""
    if os.path.exists(MASTER_FILE):
        df = pd.read_csv(MASTER_FILE, dtype=str)
        # Asegurar que fecha_vigencia sea datetime
        df['fecha_vigencia'] = pd.to_datetime(df['fecha_vigencia'], dayfirst=True, errors='coerce')
        return df
    else:
        return pd.DataFrame()

def actualizar_master(df_nuevo: pd.DataFrame, df_master: pd.DataFrame):
    """Agrega registros nuevos al archivo maestro sin duplicar datos."""
    df_nuevo = df_nuevo.copy()
    df_master = df_master.copy()

    # Asegura que 'fecha_vigencia' esté en formato datetime
    df_nuevo['fecha_vigencia'] = pd.to_datetime(df_nuevo['fecha_vigencia'], dayfirst=True, errors='coerce')
    if not df_master.empty:
        df_master['fecha_vigencia'] = pd.to_datetime(df_master['fecha_vigencia'], dayfirst=True, errors='coerce')

    # Concatenar y eliminar duplicados por claves importantes
    df_total = pd.concat([df_master, df_nuevo], ignore_index=True)
    df_total.drop_duplicates(
        subset=['cuit', 'fecha_vigencia', 'idproducto', 'tipohorario', 'precio'], inplace=True
    )

    # Ordenar por fecha
    df_total.sort_values(by='fecha_vigencia', inplace=True)

    # Guardar archivo actualizado
    df_total.to_csv(MASTER_FILE, index=False)
    logging.info(f"Archivo maestro actualizado con {len(df_total)} registros.")

    return df_total

def main():
    logging.info("Iniciando proceso de actualización de precios de combustibles...")
    ensure_directories()

    api = APIGobierno()

    if not api.is_online():
        logging.warning("La API del gobierno no está disponible. Abortando.")
        return

    try:
        df_nuevo = api.get_gas_prices_dataframe()

        if df_nuevo is not None and not df_nuevo.empty:
            logging.info(f"Datos nuevos obtenidos: {len(df_nuevo)} registros.")
            df_master = cargar_master()
            df_actualizado = actualizar_master(df_nuevo, df_master)

            # Mostrar resumen fechas
            fecha_min = df_actualizado['fecha_vigencia'].min()
            fecha_max = df_actualizado['fecha_vigencia'].max()
            print("\nResumen del archivo maestro actualizado:")
            print(f"Fecha vigencia más antigua: {fecha_min}")
            print(f"Fecha vigencia más reciente: {fecha_max}")

        else:
            logging.warning("No se recibieron datos nuevos desde la API.")

    except Exception as e:
        logging.error(f"Error inesperado: {e}", exc_info=True)

if __name__ == "__main__":
    main()
