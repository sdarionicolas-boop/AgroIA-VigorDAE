
import torch
import torch.nn as nn
import numpy as np
import logging
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

class LSTMAutoencoder(nn.Module):
    def __init__(self, input_dim, hidden_dim, seq_len):
        super(LSTMAutoencoder, self).__init__()
        self.seq_len = seq_len
        self.encoder = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.decoder = nn.LSTM(hidden_dim, hidden_dim, batch_first=True)
        self.output_layer = nn.Linear(hidden_dim, input_dim)
        
    def forward(self, x):
        _, (hidden, _) = self.encoder(x)
        repeat_hidden = hidden.repeat(self.seq_len, 1, 1).transpose(0, 1)
        decoder_out, _ = self.decoder(repeat_hidden)
        return self.output_layer(decoder_out)

class DAEVerifier:
    """
    Agente de Auditoría basado en Denoising Autoencoder.
    """
    def __init__(self, input_dim=1, hidden_dim=32, seq_len=8):
        self.seq_len = seq_len
        self.model = LSTMAutoencoder(input_dim, hidden_dim, seq_len)
        self.scaler = StandardScaler()
        self.threshold = None

    def _create_sequences(self, data):
        return np.array([data[i : i + self.seq_len] for i in range(len(data) - self.seq_len + 1)])

    def train(self, series, epochs=100, lr=0.001):
        logger.info(f"Entrenando DAE con serie de longitud {len(series)}...")
        data_scaled = self.scaler.fit_transform(series.reshape(-1, 1))
        X = self._create_sequences(data_scaled)
        X_tensor = torch.tensor(X, dtype=torch.float32)
        
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()
        
        self.model.train()
        for epoch in range(epochs):
            optimizer.zero_grad()
            output = self.model(X_tensor)
            loss = criterion(output, X_tensor)
            loss.backward()
            optimizer.step()
        
        self.model.eval()
        with torch.no_grad():
            reconstructed = self.model(X_tensor)
            mse = torch.mean((X_tensor - reconstructed)**2, dim=(1, 2)).numpy()
            self.threshold = np.percentile(mse, 95)
        
        logger.info(f"Entrenamiento completado. Umbral: {self.threshold:.6f}")

    def audit(self, series):
        if self.threshold is None:
            raise ValueError("El modelo no ha sido entrenado.")
            
        data_scaled = self.scaler.transform(series.reshape(-1, 1))
        X = self._create_sequences(data_scaled)
        X_tensor = torch.tensor(X, dtype=torch.float32)
        
        self.model.eval()
        with torch.no_grad():
            reconstructed_scaled = self.model(X_tensor).numpy()
            
        cleaned_scaled = np.copy(data_scaled)
        mask = np.zeros(len(series), dtype=bool)
        mse_seq = np.mean((X - reconstructed_scaled)**2, axis=(1, 2))
        
        for i in range(len(mse_seq)):
            if mse_seq[i] > self.threshold:
                mask[i : i + self.seq_len] = True
                cleaned_scaled[i : i + self.seq_len] = reconstructed_scaled[i]

        cleaned_series = self.scaler.inverse_transform(cleaned_scaled).flatten()
        return cleaned_series, mask
