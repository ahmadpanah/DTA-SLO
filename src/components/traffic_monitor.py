from src.models.data_models import TrafficMetrics
from typing import Dict, List
import threading
import time
from collections import defaultdict

class TrafficMonitor:
    def __init__(self, sampling_interval: float = 1.0):
        self.sampling_interval = sampling_interval
        self.traffic_data = defaultdict(lambda: defaultdict(list))
        self.live_metrics = defaultdict(lambda: defaultdict(TrafficMetrics))
        self.lock = threading.Lock()
        self.running = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop)
        self.monitoring_thread.start()

    def _monitor_loop(self):
        while self.running:
            self._collect_metrics()
            time.sleep(self.sampling_interval)

    def _collect_metrics(self):
        with self.lock:
            current_time = time.time()
            for service_id in self.live_metrics:
                for chain_id in self.live_metrics[service_id]:
                    metrics = self.live_metrics[service_id][chain_id]
                    self.traffic_data[service_id][chain_id].append({
                        'timestamp': current_time,
                        'rps': metrics.requests_per_second,
                        'response_time': metrics.response_time,
                        'error_rate': metrics.error_rate
                    })

    def record_request(self, service_id: str, chain_id: str, response_time: float, is_error: bool = False):
        with self.lock:
            current_time = time.time()
            metrics = self.live_metrics[service_id][chain_id]
            
            # Update RPS using sliding window
            window_size = 60  # 1 minute window
            current_window = self.traffic_data[service_id][chain_id]
            current_window = [x for x in current_window 
                            if x['timestamp'] > current_time - window_size]
            
            metrics.requests_per_second = len(current_window) / window_size
            metrics.response_time = response_time
            metrics.error_rate = (metrics.error_rate * len(current_window) + int(is_error)) / (len(current_window) + 1)
            metrics.timestamp = current_time

    def get_metrics(self, service_id: str, chain_id: str, 
                   time_window: float = 300) -> List[Dict]:
        with self.lock:
            current_time = time.time()
            return [
                metric for metric in self.traffic_data[service_id][chain_id]
                if metric['timestamp'] > current_time - time_window
            ]

    def stop(self):
        self.running = False
        self.monitoring_thread.join()