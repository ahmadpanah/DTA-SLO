# DTA-SLO: Dynamic Traffic-Aware SLO Allocation Framework

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)

A robust framework for optimizing resource management in complex microservice deployments with shared services and multi-chain dependencies. DTA-SLO leverages real-time traffic monitoring, time-series prediction using GRU (Gated Recurrent Unit), and novel optimization approaches to dynamically allocate resources based on individual service chain SLOs.

## 🌟 Key Features

- **Real-time Traffic Monitoring**: Continuous monitoring of service metrics including request rates, latency, and error rates
- **ML-Powered Traffic Prediction**: Advanced time-series forecasting using GRU neural networks
- **Dynamic Resource Optimization**: Intelligent resource allocation based on current and predicted workloads
- **SLO-Driven Management**: Ensures service level objectives are met across all service chains
- **Kubernetes Integration**: Native support for Kubernetes deployments with rolling updates
- **Multi-Chain Awareness**: Handles complex dependencies between microservices
- **Performance Impact Analysis**: Quantifies the impact of shared services on overall system performance

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Kubernetes cluster (for deployment)
- kubectl configured with cluster access

### Installation

1. Clone the repository:
```bash
git clone https://github.com/ahmadpanah/dta-slo.git
cd dta-slo
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage

1. Configure your services in `config/config.yaml`:
```yaml
services:
  auth-service:
    chains:
      - user-registration
      - order-processing
    min_cpu: 0.1
    max_cpu: 4.0
    min_memory: 128
    max_memory: 8192

slos:
  user-registration: 0.2  # 200ms
  order-processing: 0.5  # 500ms
```

2. Run the framework:
```bash
python main.py
```

## 📁 Project Structure

```
dta_slo/
│
├── __init__.py
├── requirements.txt
├── config/
│   └── config.yaml
│
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── data_models.py
│   │   └── metrics.py
│   │
│   ├── components/
│   │   ├── traffic_monitor.py
│   │   ├── traffic_predictor.py
│   │   ├── performance_quantifier.py
│   │   └── resource_allocator.py
│   │
│   └── utils/
│       └── kubernetes_utils.py
│
└── main.py
```

## 🔧 Core Components

### Traffic Monitor
Collects and processes real-time service metrics:
```python
traffic_monitor = TrafficMonitor(sampling_interval=1.0)
traffic_monitor.record_request("auth-service", "user-registration", 0.15)
```

### Traffic Predictor
Forecasts future traffic patterns using GRU:
```python
predictor = TrafficPredictor(sequence_length=60, prediction_horizon=10)
future_load = predictor.predict(historical_data)
```

### Resource Allocator
Optimizes resource allocation based on traffic and SLOs:
```python
allocator = DynamicResourceAllocator(traffic_monitor, traffic_predictor, performance_quantifier)
new_allocations = allocator.optimize_resources(services, slos)
```

## 📊 Performance Metrics

DTA-SLO tracks several key metrics:
- Resource Utilization
- SLO Violation Rate
- Average End-to-End Latency
- Fairness Index (resource distribution)

## 🔍 Configuration Options

### Monitoring Settings
```yaml
monitoring:
  sampling_interval: 1.0  # seconds
  window_size: 3600      # seconds
```

### Prediction Settings
```yaml
prediction:
  sequence_length: 60
  prediction_horizon: 10
  feature_dim: 3
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 📧 Contact

- Seyed Hossein Ahmadpanah - h.ahmadpanah@iau.ac.ir
- Meghdad Mirabi - meghdad.mirabi@cs.tu-darmstadt.de
