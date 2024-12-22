import tensorflow as tf
from tensorflow.keras.layers import GRU, Dense, Dropout, BatchNormalization
from tensorflow.keras.models import Sequential
import numpy as np
from typing import Tuples

class TrafficPredictor:
    def __init__(self, 
                 sequence_length: int = 60,
                 prediction_horizon: int = 10,
                 feature_dim: int = 3):
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.feature_dim = feature_dim
        self.model = self._build_model()
        self.scaler = None

    def _build_model(self) -> Sequential:
        model = Sequential([
            # First GRU layer with sequence input
            GRU(128, input_shape=(self.sequence_length, self.feature_dim),
                return_sequences=True),
            BatchNormalization(),
            Dropout(0.2),
            
            # Second GRU layer
            GRU(64, return_sequences=True),
            BatchNormalization(),
            Dropout(0.2),
            
            # Third GRU layer
            GRU(32),
            BatchNormalization(),
            Dropout(0.2),
            
            # Dense layers for output
            Dense(64, activation='relu'),
            Dense(32, activation='relu'),
            Dense(self.prediction_horizon)
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        return model

    def prepare_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        X, y = [], []
        for i in range(len(data) - self.sequence_length - self.prediction_horizon + 1):
            X.append(data[i:(i + self.sequence_length)])
            y.append(data[(i + self.sequence_length):(i + self.sequence_length + self.prediction_horizon), 0])
        return np.array(X), np.array(y)

    def train(self, historical_data: np.ndarray, epochs: int = 100, 
             batch_size: int = 32, validation_split: float = 0.2):
        # Normalize data
        if self.scaler is None:
            self.scaler = StandardScaler()
            historical_data = self.scaler.fit_transform(historical_data)
        else:
            historical_data = self.scaler.transform(historical_data)

        X, y = self.prepare_sequences(historical_data)
        
        # Train model with early stopping
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stopping],
            verbose=1
        )

    def predict(self, recent_data: np.ndarray) -> np.ndarray:
        if self.scaler is not None:
            recent_data = self.scaler.transform(recent_data)
        
        X = recent_data[-self.sequence_length:].reshape(1, self.sequence_length, self.feature_dim)
        predictions = self.model.predict(X, verbose=0)
        
        if self.scaler is not None:
            # Inverse transform only the traffic predictions
            predictions_reshaped = np.zeros((len(predictions[0]), self.feature_dim))
            predictions_reshaped[:, 0] = predictions[0]
            predictions = self.scaler.inverse_transform(predictions_reshaped)[:, 0]
        
        return predictions