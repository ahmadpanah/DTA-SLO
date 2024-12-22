from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np

@dataclass
class PerformanceMetrics:
    expected_latency: float
    confidence: float
    risk_factor: float

class LoadLatencyProfile:
    def __init__(self, service_id: str, chain_id: str):
        self.service_id = service_id
        self.chain_id = chain_id
        self.load_points: List[float] = []
        self.latency_points: List[float] = []
        self.error_points: List[float] = []
        self.regression_model: Optional[tuple] = None