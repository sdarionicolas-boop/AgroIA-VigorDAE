
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

class LSTMAutoencoder(nn.Module):
    """
    Arquitectura Encoder-Decoder LSTM para auditoría de series temporales.
    Inspirado en Agro-DAE-Auditor.
    """
    def __init__(self, input_dim, hidden_dim, seq_len):
        super(LSTMAutoencoder, self).__init__()
        self.seq_len = seq_len
        self.input_dim = input_dim
        
        # Encoder
        self.encoder = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        
        # Decoder
        self.decoder = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
        self.output_layer = nn.Linear(hidden_dim, input_dim)
        
    def forward(self, x):
        # Encoder: x shape (batch, seq_len, input_dim)
        _, (hidden, _) = self.encoder(x)
        # hidden shape (1, batch, hidden_dim)
        
        # Repeat hidden state for decoder
        # We want (batch, seq_len, hidden_dim)
        repeat_hidden = hidden.repeat(self.seq_len, 1, 1).transpose(0, 1)
        
        # Decoder
        decoder_out, _ = self.decoder(repeat_hidden)
        out = self.output_layer(decoder_out)
        return out

class DAEVerifierAgent:
    """
    Agente verificador que utiliza un Denoising Autoencoder para 
    detectar y corregir anomalías en series temporales agrícolas.
    """
    def __init__(self, input_dim=1, hidden_dim=16, seq_len=10, lr=0.001):
        self.seq_len = seq_len
        self.input_dim = input_dim
        self.model = LSTMAutoencoder(input_dim, hidden_dim, seq_len)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        self.criterion = nn.MSELoss()
        self.scaler = StandardScaler()
        self.threshold = None

    def _create_sequences(self, data):
        sequences = []
        for i in range(len(data) - self.seq_len + 1):
            sequences.append(data[i : i + self.seq_len])
        return np.array(sequences)

    def train_agent(self, series, epochs=50, batch_size=32):
        """
        Entrena el agente con una serie temporal (ej. NDVI).
        Asume que la serie es mayormente limpia o que el DAE aprenderá el patrón robusto.
        """
        # Escalar datos
        data_scaled = self.scaler.fit_transform(series.reshape(-1, 1))
        
        # Crear secuencias
        X = self._create_sequences(data_scaled)
        X_tensor = torch.tensor(X, dtype=torch.float32)
        
        self.model.train()
        for epoch in range(epochs):
            self.optimizer.zero_grad()
            output = self.model(X_tensor)
            loss = self.criterion(output, X_tensor)
            loss.backward()
            self.optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                print(f"  Epoch [{epoch+1}/{epochs}], Loss: {loss.item():.6f}")

        # Calcular umbral de anomalía (percentil 95 del error de reconstrucción)
        self.model.eval()
        with torch.no_grad():
            reconstructed = self.model(X_tensor)
            mse = torch.mean((X_tensor - reconstructed)**2, dim=(1, 2)).numpy()
            self.threshold = np.percentile(mse, 95)
            print(f"[OK] Agente entrenado. Umbral de anomalía: {self.threshold:.6f}")

    def audit_series(self, series):
        """
        Audita una serie completa. Devuelve:
        - cleaned_series: Serie con valores anómalos reemplazados por la reconstrucción.
        - anomaly_scores: Score de error para cada punto.
        - mask: Booleano donde True significa anomalía detectada.
        """
        if self.threshold is None:
            raise ValueError("El agente debe ser entrenado antes de auditar.")

        data_scaled = self.scaler.transform(series.reshape(-1, 1))
        X = self._create_sequences(data_scaled)
        X_tensor = torch.tensor(X, dtype=torch.float32)
        
        self.model.eval()
        with torch.no_grad():
            reconstructed_scaled = self.model(X_tensor).numpy()
            
        # El modelo reconstruye secuencias de seq_len. 
        # Para obtener la serie punto a punto, promediamos o tomamos el último.
        # Aquí tomaremos el valor central de la reconstrucción para mayor estabilidad.
        
        cleaned_scaled = np.copy(data_scaled)
        anomaly_scores = np.zeros(len(series))
        mask = np.zeros(len(series), dtype=bool)
        
        # Calcular error por secuencia
        mse_seq = np.mean((X - reconstructed_scaled)**2, axis=(1, 2))
        
        for i in range(len(mse_seq)):
            if mse_seq[i] > self.threshold:
                # Marcar la secuencia como anómala
                idx_start = i
                idx_end = i + self.seq_len
                mask[idx_start:idx_end] = True
                # Reemplazar valores anómalos por la reconstrucción (des-escalada)
                recon_vals = self.scaler.inverse_transform(reconstructed_scaled[i])
                cleaned_scaled[idx_start:idx_end] = reconstructed_scaled[i]
                anomaly_scores[idx_start:idx_end] = mse_seq[i]

        cleaned_series = self.scaler.inverse_transform(cleaned_scaled).flatten()
        return cleaned_series, anomaly_scores, mask
