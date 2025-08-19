"""
Government's API client
"""
import logging

from dataclasses import dataclass
from pandas import read_csv, DataFrame
from numpy import percentile
from requests.exceptions import RequestException

from .dataset import DatasetResponse
from .http import HttpClient
from .io import FileName


@dataclass
class APIGobierno:
    """
    Argentina government's API (Foreign)
    """

    API_URL = "https://datos.gob.ar/api/3"
    DATASET_ID = "energia-precios-surtidor---resolucion-3142016"
    URL_PATHs = {"get_dataset": "action/package_show"}
    RESOURCE_NAME = "Precios vigentes en surtidor - Resolución 314/2016"

    def dataset_url(self):
        """
        Get the predefined Dataset's URL.
        """
        url = (
            f"{self.API_URL}/{self.URL_PATHs['get_dataset']}"
            f"?id={self.DATASET_ID}"
        )
        return url

    def is_online(self):
        """
        Verify whether the foreign API service is online.
        Any request-related exception is interpreted as the
        service being offline.
        """
        try:
            HttpClient.http_request(self.API_URL)
            is_online = True
        except RequestException:
            is_online = False
        return is_online

    def get_dataset_metadata(self):
        """
        Challenge the foreign API to get metadata for the
        dataset.
        """
        response = HttpClient.api_call(self.dataset_url())
        try:
            if isinstance(response, dict):
                dataset = DatasetResponse(response)
            else:
                raise RuntimeError(
                    "Unable to fetch Dataset" f"metadata. Got: {response}"
                )
        except ValueError as exc:
            raise RuntimeError(
                "Unable to parse Dataset" f"metadata. Got: {response}"
            ) from exc
        return dataset

    def get_gas_prices_resource(self):
        """
        Get the resource containing the gas-prices Dataset, as defined
        in the API's metadata response.
        """
        response = None
        try:
            dsmetadata = self.get_dataset_metadata()
            if dsmetadata is not None:
                rsmetadata = dsmetadata.get_resource(self.RESOURCE_NAME)
                if rsmetadata is not None:
                    response = HttpClient.http_download(rsmetadata.url)
        except KeyError:
            pass
        return response

    def get_gas_prices_resource_file(self, outfile: str):
        """
        Get the resource containing the gas-prices Dataset, as defined
        in the API's metadata response.
        The output is saved to a file in disk.
        """
        downloaded = False
        try:
            dsmetadata = self.get_dataset_metadata()
            if dsmetadata is not None:
                rsmetadata = dsmetadata.get_resource(self.RESOURCE_NAME)
                if rsmetadata is not None:
                    downloaded = HttpClient.http_download_as_file(
                        rsmetadata.url, outfile
                    )
        except KeyError:
            pass
        return downloaded

    def get_gas_prices_dataframe(self):
        """
        Always download the latest dataset and load it as a DataFrame.
        """
        file = FileName("tmp_datasource.csv")

        # Siempre descarga el dataset más reciente
        logging.info("Descargando dataset más reciente desde la API...")
        download = self.get_gas_prices_resource_file(file.full_name)
        if not download:
            logging.error("No se pudo descargar el dataset.")
            return None

        try:
            df = read_csv(file.full_name)
            logging.debug("Dataframe leído: \n%s", df.info())
        except ValueError as exc:
            logging.error("Error al leer el archivo CSV: %s", exc)
            return None

        return df

