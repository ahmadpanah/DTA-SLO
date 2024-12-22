from src.models.metrics import PerformanceMetrics, LoadLatencyProfile
from typing import Dict, List, Optional
import numpy as np
from scipy.stats import linregress

class PerformanceProfile:
    def __init__(self, service_id: str, chain_id: str):
        self.service_id = service_id
        self.chain_id = chain_id
        self.load_points: List[float] = []
        self.latency_points: List[float] = []
        self.error_points: List[float] = []
        self.regression_model: Optional[tuple] = None

    def update(self, load: float, latency: float, error_rate: float):
        self.load_points.append(load)
        self.latency_points.append(latency)
        self.error_points.append(error_rate)
        
        # Update regression model if we have enough points
        if len(self.load_points) >= 2:
            self.regression_model = linregress(self.load_points, self.latency_points)

    def predict_latency(self, load: float) -> float:
        if self.regression_model is None:
            return 0.0
        slope, intercept, _, _, _ = self.regression_model
        return slope * load + intercept

class PerformanceImpactQuantifier:
    def __init__(self):
        self.profiles: Dict[str, Dict[str, PerformanceProfile]] = {}
        self.window_size = 3600  # 1 hour window for performance analysis

    def update_profile(self, 
                      service_id: str, 
                      chain_id: str, 
                      metrics: Dict[str, float]):
        if service_id not in self.profiles:
            self.profiles[service_id] = {}
        
        if chain_id not in self.profiles[service_id]:
            self.profiles[service_id][chain_id] = PerformanceProfile(service_id, chain_id)

        self.profiles[service_id][chain_id].update(
            load=metrics['rps'],
            latency=metrics['response_time'],
            error_rate=metrics['error_rate']
        )

    def analyze_impact(self, 
                      service_id: str, 
                      chain_id: str, 
                      predicted_load: float) -> Dict[str, float]:
        if (service_id not in self.profiles or 
            chain_id not in self.profiles[service_id]):
            return {
                'expected_latency': 0.0,
                'confidence': 0.0,
                'risk_factor': 1.0
            }

        profile = self.profiles[service_id][chain_id]
        
        # Calculate expected latency
        expected_latency = profile.predict_latency(predicted_load)
        
        # Calculate confidence based on data points
        n_points = len(profile.load_points)
        confidence = min(1.0, n_points / 100)  # Normalize by 100 data points
        
        # Calculate risk factor based on error rates
        recent_errors = np.mean(profile.error_points[-10:]) if len(profile.error_points) >= 10 else 0
        risk_factor = 1.0 + recent_errors
        
        return {
            'expected_latency': expected_latency,
            'confidence': confidence,
            'risk_factor': risk_factor
        }

    def get_load_latency_profile(self, 
                                service_id: str, 
                                chain_id: str) -> Dict[str, List[float]]:
        if (service_id not in self.profiles or 
            chain_id not in self.profiles[service_id]):
            return {'loads': [], 'latencies': [], 'errors': []}

        profile = self.profiles[service_id][chain_id]
        return {
            'loads': profile.load_points,
            'latencies': profile.latency_points,
            'errors': profile.error_points
        }