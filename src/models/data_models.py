from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime

@dataclass
class TrafficMetrics:
    requests_per_second: float
    response_time: float
    timestamp: float
    error_rate: float

@dataclass
class ResourceAllocation:
    cpu: float
    memory: float
    instances: int

@dataclass
class ServiceConfig:
    service_id: str
    chains: List[str]
    min_cpu: float
    max_cpu: float
    min_memory: float
    max_memory: float