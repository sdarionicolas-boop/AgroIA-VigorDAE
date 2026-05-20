
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

    def analyze_season(self, series_ndvi, dates, filtrar_ultimo_anio: bool = True):
        """
        Calcula inicio, pico y fin de campaña.
        """
        try:
            df_f = pd.DataFrame({"time": pd.to_datetime(dates), "ndvi": series_ndvi})
            
            if filtrar_ultimo_anio:
                cutoff = df_f["time"].max() - pd.DateOffset(months=12)
                df_f = df_f[df_f["time"] >= cutoff].reset_index(drop=True)
            
            if len(df_f) < 5:
                return None

            series = df_f["ndvi"].ffill().fillna(0).values
            dates_arr = df_f["time"].values
            
            # Suavizado para estabilidad
            smooth = gaussian_filter1d(series, sigma=self.params["sigma"])
            
            # Pico: máximo absoluto en el rango filtrado
            peak_idx = int(np.nanargmax(smooth))
            peak_value = smooth[peak_idx]
            peak_date = pd.Timestamp(dates_arr[peak_idx])
            
            # Inicio: primer punto que supera el umbral antes del pico
            pre_peak = smooth[:peak_idx] if peak_idx > 0 else smooth
            start_mask = pre_peak > self.params["ndvi_start"]
            start_idx = int(np.argmax(start_mask)) if np.any(start_mask) else 0
            
            # Fin: primer punto después del pico que cae bajo el umbral dinámico
            # Limitado a 548 días post-pico (1.5 años)
            max_end_date = peak_date + pd.DateOffset(days=548)
            post_peak_indices = np.where(pd.to_datetime(dates_arr) >= peak_date)[0]
            dates_post = pd.to_datetime(dates_arr[post_peak_indices])
            valid_post_mask = dates_post <= max_end_date
            
            smooth_post = smooth[post_peak_indices][valid_post_mask]
            
            # Umbral de fin dinámico (50% del pico o el mínimo de inicio)
            end_threshold = max(peak_value * 0.5, self.params["ndvi_start"])
            end_mask = smooth_post < end_threshold
            
            results = {
                "inicio": pd.Timestamp(dates_arr[start_idx]),
                "pico": peak_date,
                "fin": None,
                "duracion_dias": None
            }
            
            if np.any(end_mask):
                local_end_idx = int(np.argmax(end_mask))
                end_idx = post_peak_indices[0] + local_end_idx
                results["fin"] = pd.Timestamp(dates_arr[end_idx])
                results["duracion_dias"] = (results["fin"] - results["inicio"]).days
            
            return results
        except Exception as e:
            logger.error(f"Error en analisis fenologico: {e}")
            return None

