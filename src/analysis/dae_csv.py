import pandas as pd
import numpy as np
import sys
import os

# Asegurar que podemos importar desde src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from src.models.verifier import DAEVerifier
    HAS_VERIFIER = True
except ImportError:
    HAS_VERIFIER = False
    class DAEVerifier:
        def __init__(self, **kwargs): pass
        def train(self, series): pass
        def audit(self, series):
            # Dummy fallback: no se detectan anomalías
            return series.copy(), np.zeros_like(series, dtype=bool)

def audit_indices(df: pd.DataFrame, dae_params: dict) -> pd.DataFrame:
    """
    Auditoría para series temporales de índices en CSV usando DAE-LSTM.
    """
    if not HAS_VERIFIER:
        print(">>> WARNING: DAEVerifier not found in src.models.verifier. Using dummy fallback.")
    
    df_audit = df.copy()
    
    # Lista de columnas que son índices (evitando 'fecha')
    indices = [c for k, c in enumerate(df.columns) if c != 'fecha' and not c.endswith('_auditado') and not c.endswith('_anomalia')]
    
    if len(df) < 10:
        print(">>> WARNING: Serie demasiado corta (<10 puntos) para auditar con DAE.")
        for idx in indices:
            df_audit[f"{idx}_auditado"] = df[idx]
            df_audit[f"{idx}_anomalia"] = False
        return df_audit

    # Parámetros admitidos por el constructor (DAEVerifier.__init__)
    # Según verifier.py: input_dim=1, hidden_dim=32, seq_len=6
    valid_init_keys = ['input_dim', 'hidden_dim', 'seq_len']
    init_params = {k: v for k, v in dae_params.items() if k in valid_init_keys}
    
    # Parámetros para el método train
    epochs = dae_params.get('epochs', 50)
    lr = dae_params.get('lr', 0.001)
    
    for idx in indices:
        try:
            print(f">>> DEBUG: Auditing index {idx} with DAE...")
            # Preparar serie (debe ser 1D)
            series = df[idx].values
            
            # Instanciar solo con parámetros de arquitectura
            verifier = DAEVerifier(**init_params)
            
            # Entrenar pasando hiperparámetros de optimización
            verifier.train(series, epochs=epochs, lr=lr)
            auditado, anomalias = verifier.audit(series)
            
            df_audit[f"{idx}_auditado"] = np.round(auditado, 4)
            df_audit[f"{idx}_anomalia"] = anomalias.astype(bool)
            
        except Exception as e:
            print(f">>> ERROR auditing {idx}: {e}")
            # Fallback a la serie original si falla el modelo
            df_audit[f"{idx}_auditado"] = df[idx]
            df_audit[f"{idx}_anomalia"] = False
            
    return df_audit
