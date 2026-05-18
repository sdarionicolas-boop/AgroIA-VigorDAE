
import os
import glob
import re
import logging
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray
from src.config.settings import DATA_RAW_DIR, DATACUBE_RAW_PATH, CRS_EPSG, BANDAS_S2

logger = logging.getLogger(__name__)

class DataIngestor:
    """
    Se encarga de transformar imágenes TIFF de Sentinel-2 en un DataCube (NetCDF).
    """
    def __init__(self, raw_dir=DATA_RAW_DIR, output_path=DATACUBE_RAW_PATH):
        self.raw_dir = raw_dir
        self.output_path = output_path

    def discover_files(self, pattern="MANI_*.tif"):
        """Busca archivos TIFF siguiendo el patrón."""
        files = sorted(glob.glob(str(self.raw_dir / pattern)))
        if not files:
            # Fallback a S2_*.tif si no hay MANI_
            files = sorted(glob.glob(str(self.raw_dir / "S2_*.tif")))
            
        logger.info(f"Encontrados {len(files)} archivos TIFF en {self.raw_dir}")
        return files

    def extract_date(self, filename):
        """Extrae la fecha YYYYMMDD del nombre del archivo."""
        match = re.search(r'(\d{8})', os.path.basename(filename))
        return match.group(1) if match else None

    def process_to_datacube(self, pattern="MANI_*.tif"):
        """Ejecuta el pipeline de ingesta completo."""
        files = self.discover_files(pattern)
        if not files:
            logger.error("No hay archivos para procesar.")
            return None

        da_list = []
        fechas = []

        for f in files:
            date_str = self.extract_date(f)
            if not date_str:
                logger.warning(f"No se pudo extraer fecha de {f}. Saltando...")
                continue
            
            logger.info(f"Procesando fecha: {date_str}")
            da = rioxarray.open_rasterio(f, chunks={'x': 1000, 'y': 1000})
            nband = da.sizes.get("band", 1)

            # Estandarizar a 9 bandas (Sentinel-2 base + índices)
            if nband == 9:
                da = da.assign_coords(band=BANDAS_S2)
            elif nband == 5:
                # Calcular índices al vuelo si faltan
                base_names = ['B2','B3','B4','B5','B8']
                da = da.assign_coords(band=base_names)
                dsb = da.to_dataset(dim="band")
                eps = 1e-10
                NDVI = (dsb['B8'] - dsb['B4']) / (dsb['B8'] + dsb['B4'] + eps)
                NDRE = (dsb['B8'] - dsb['B5']) / (dsb['B8'] + dsb['B5'] + eps)
                NDWI = (dsb['B3'] - dsb['B8']) / (dsb['B3'] + dsb['B8'] + eps)
                EVI  = 2.5 * ((dsb['B8'] - dsb['B4']) / (dsb['B8'] + 6*dsb['B4'] - 7.5*dsb['B2'] + 1 + eps))
                
                da = xr.concat(
                    [dsb['B2'], dsb['B3'], dsb['B4'], dsb['B5'], dsb['B8'], NDVI, NDRE, NDWI, EVI],
                    dim="band"
                ).assign_coords(band=BANDAS_S2)
            
            da = da.astype("float32")
            da_list.append(da)
            fechas.append(date_str)

        # Concatenar y asignar tiempo
        logger.info("Concatenando serie temporal...")
        datacube = xr.concat(da_list, dim="time")
        fechas_dt = pd.to_datetime(fechas, format="%Y%m%d")
        datacube = datacube.assign_coords(time=fechas_dt)
        datacube = datacube.to_dataset(dim="band")

        # Asegurar CRS
        if datacube.rio.crs is None:
            datacube.rio.write_crs(CRS_EPSG, inplace=True)

        # Guardar
        logger.info(f"Guardando DataCube Raw en {self.output_path}")
        encoding = {var: {'zlib': True, 'complevel': 1} for var in datacube.data_vars}
        datacube.to_netcdf(self.output_path, engine='netcdf4', encoding=encoding)
        
        logger.info("Ingesta completada satisfactoriamente.")
        return datacube

if __name__ == "__main__":
    from src.config.logging_config import setup_logging
    setup_logging()
    ingestor = DataIngestor()
    ingestor.process_to_datacube()
