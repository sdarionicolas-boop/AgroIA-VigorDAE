
import logging
import numpy as np
import pandas as pd
from scipy import stats
from scipy.ndimage import gaussian_filter1d
from src.config.settings import FENO_PARAMS

logger = logging.getLogger(__name__)

class PhenologyAnalyzer:
    """
    Analiza las etapas de crecimiento del cultivo (fenología).
    """
    def __init__(self, params=FENO_PARAMS):
        self.params = params

    def analyze_season(self, series_ndvi, dates):
        """
        Calcula inicio, pico y fin de campaña.
        """
        if len(series_ndvi) < 10 or np.all(np.isnan(series_ndvi)):
            return None

        try:
            # Suavizado para estabilidad
            ndvi_smooth = gaussian_filter1d(series_ndvi, sigma=self.params["sigma"])
            
            # Inicio: primer punto que supera el umbral
            start_mask = ndvi_smooth > self.params["ndvi_start"]
            start_idx = np.argmax(start_mask) if np.any(start_mask) else None
            
            # Pico: máximo absoluto
            peak_idx = int(np.nanargmax(ndvi_smooth)) if not np.all(np.isnan(ndvi_smooth)) else None
            
            # Fin: primer punto después del pico que cae bajo el umbral
            end_idx = None
            if peak_idx is not None and peak_idx < len(ndvi_smooth) - 1:
                end_mask = ndvi_smooth[peak_idx:] < self.params["ndvi_end"]
                end_idx = peak_idx + np.argmax(end_mask) if np.any(end_mask) else len(ndvi_smooth) - 1

            results = {
                'inicio': dates[start_idx] if start_idx is not None else None,
                'pico': dates[peak_idx] if peak_idx is not None else None,
                'fin': dates[end_idx] if end_idx is not None else None
            }
            
            if results['inicio'] and results['fin']:
                results['duracion_dias'] = (pd.to_datetime(results['fin']) - pd.to_datetime(results['inicio'])).days
            
            return results
        except Exception as e:
            logger.error(f"Error en análisis fenológico: {e}")
            return None
