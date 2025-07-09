import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import logging

from src.data.ingestion.api_gobierno import APIGobierno
from src.cleaning.cleaner import limpiar_dataframe
from src.cleaning.limpieza_avanzada import limpieza_profunda
from src.utils.geojson_exporter import exportar_geojson


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
    if os.path.exists(MASTER_FILE):
        df = pd.read_csv(MASTER_FILE)
        fechas_invalidas = df[~pd.to_datetime(df["fecha_vigencia"], errors="coerce").notna()]
        print(f"Fechas unicas invalidas: {fechas_invalidas['fecha_vigencia'].unique()}\n")

        # Forzar conversión segura a datetime para fecha_vigencia
        df['fecha_vigencia'] = pd.to_datetime(df['fecha_vigencia'], errors='coerce', format='%Y-%m-%d %H:%M:%S')

        # Opcional: eliminar filas con fechas inválidas (NaT)
        nulos = df['fecha_vigencia'].isna().sum()
        if nulos > 0:
            print(f"\n⚠️ Advertencia: Se encontraron {nulos} fechas inválidas y se eliminarán.")
            df = df.dropna(subset=['fecha_vigencia'])
        
        print("📄 Archivo master cargado.")
        print(f"🔢 Registros cargados: {len(df)}")
        print("🗓️ Rango de fechas en master:")
        print("    ➤ Min:", df["fecha_vigencia"].min())
        print("    ➤ Max:", df["fecha_vigencia"].max())
        print("📋 Tipos de datos:")
        print(df.dtypes)
        return df
    else:
        print("📁 No se encontró el archivo maestro.")
        return pd.DataFrame()





def actualizar_master(df_nuevo: pd.DataFrame, df_master: pd.DataFrame) -> pd.DataFrame:
    df_nuevo = df_nuevo.copy()
    df_nuevo['fecha_vigencia'] = pd.to_datetime(df_nuevo['fecha_vigencia'], errors='coerce')
    df_nuevo = df_nuevo.dropna(subset=['fecha_vigencia'])

    fecha_ahora = pd.Timestamp.now()

    print(f"\n📥 Mínima fecha en datos nuevos: {df_nuevo['fecha_vigencia'].min()}")
    print(f"📥 Máxima fecha en datos nuevos: {df_nuevo['fecha_vigencia'].max()}")

    if df_master is not None and not df_master.empty and 'fecha_vigencia' in df_master.columns:
        df_master['fecha_vigencia'] = pd.to_datetime(df_master['fecha_vigencia'], errors='coerce')
        df_master = df_master.dropna(subset=['fecha_vigencia'])

        print(f"\n📦 Registros en master antes de actualizar: {len(df_master)}")
        print(f"🕓 Última fecha en master: {df_master['fecha_vigencia'].max()}")

        fecha_max_master = df_master['fecha_vigencia'].max()

        df_nuevo = df_nuevo[
            (df_nuevo['fecha_vigencia'] > fecha_max_master) &
            (df_nuevo['fecha_vigencia'] <= fecha_ahora)
        ]
        print(f"➕ Registros nuevos que se van a agregar: {len(df_nuevo)}\n")
    else:
        # No hay maestro: tomar todo lo que sea menor o igual a ahora
        df_nuevo = df_nuevo[df_nuevo['fecha_vigencia'] <= fecha_ahora]
        df_master = pd.DataFrame()

        # Eliminar duplicados exactos en los datos nuevos
        original_len = len(df_nuevo)
        df_nuevo.drop_duplicates(inplace=True)
        print(f"🧹 Registros nuevos únicos luego de eliminar duplicados exactos: {len(df_nuevo)} (eliminados {original_len - len(df_nuevo)})")


    if df_nuevo.empty:
        logging.info("No hay datos nuevos para agregar al archivo maestro.")
        return df_master
    

    df_total = pd.concat([df_master, df_nuevo], ignore_index=True)

    # 🔁 Eliminar filas completamente duplicadas (todas las columnas)
    antes_dedup = len(df_total)
    df_total.drop_duplicates(inplace=True)
    despues_dedup = len(df_total)
    print(f"🧹 Registros únicos tras eliminar duplicados exactos: {despues_dedup} (eliminados {antes_dedup - despues_dedup})")

    # Ordenar cronológicamente
    df_total.sort_values(by='fecha_vigencia', inplace=True)

    df_total.to_csv(MASTER_FILE, index=False, date_format='%Y-%m-%d %H:%M:%S')
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
            actualizado = actualizar_master(df_original, df_master)  # ← CORREGIDO
            mostrar_resumen_desde_archivo()

            combustibles_filtrados = [
                'gnc',
                'gas oil grado 2',
                'nafta super entre 92 y 95 ron',
                'nafta premium de mas de 95 ron',
                'gas oil grado 3'
            ]

            df_geo = actualizado[actualizado['producto'].str.lower().isin([c.lower() for c in combustibles_filtrados])]
            exportar_geojson(df_geo, 'mapa_combustibles/data/estaciones.geojson')
            logging.info("📦 GeoJSON exportado correctamente con datos actualizados.")

        else:           
            logging.warning("No se recibieron datos nuevos desde la API.")
            mostrar_resumen_desde_archivo()

    except Exception as e:
        logging.error(f"Error inesperado: {e}", exc_info=True)


if __name__ == "__main__":
    main()
