
import logging
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)

class StatsAnalyzer:
    """
    Cálculos estadísticos y detección de tendencias.
    """
    @staticmethod
    def calculate_trend(series):
        """Calcula la tendencia lineal simple."""
        if len(series) < 3 or np.all(np.isnan(series)):
            return None
            
        mask = ~np.isnan(series)
        x = np.arange(len(series))
        
        try:
            slope, intercept, r_val, p_val, std_err = stats.linregress(x[mask], series[mask])
            return {
                'slope': slope,
                'p_value': p_val,
                'r_squared': r_val**2,
                'is_significant': p_val < 0.05
            }
        except Exception as e:
            logger.warning(f"Error calculando tendencia: {e}")
            return None

    @staticmethod
    def detect_abrupt_changes(series, threshold=0.25):
        """Detecta saltos bruscos en la serie."""
        diffs = np.abs(np.diff(series, prepend=series[0]))
        return diffs > threshold
