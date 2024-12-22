import yaml
from src.components.traffic_monitor import TrafficMonitor
from src.components.traffic_predictor import TrafficPredictor
from src.components.performance_quantifier import PerformanceImpactQuantifier
from src.components.resource_allocator import DynamicResourceAllocator
import time

def load_config():
    with open('config/config.yaml', 'r') as f:
        return yaml.safe_load(f)

def main():
    # Load configuration
    config = load_config()
    
    # Initialize components
    traffic_monitor = TrafficMonitor(
        sampling_interval=config['monitoring']['sampling_interval']
    )
    
    traffic_predictor = TrafficPredictor(
        sequence_length=config['prediction']['sequence_length'],
        prediction_horizon=config['prediction']['prediction_horizon'],
        feature_dim=config['prediction']['feature_dim']
    )
    
    performance_quantifier = PerformanceImpactQuantifier()
    
    allocator = DynamicResourceAllocator(
        traffic_monitor,
        traffic_predictor,
        performance_quantifier
    )

    try:
        while True:
            # Optimize resources periodically
            new_allocations = allocator.optimize_resources(
                config['services'],
                config['slos']
            )
            
            # Apply new allocations
            if allocator.apply_allocations(new_allocations):
                print("Successfully updated resource allocations:")
                for service_id, allocation in new_allocations.items():
                    print(f"{service_id}: CPU={allocation.cpu}, "
                          f"Memory={allocation.memory}, "
                          f"Instances={allocation.instances}")
            
            # Wait before next optimization
            time.sleep(300)  # 5 minutes

    except KeyboardInterrupt:
        print("Shutting down...")
        traffic_monitor.stop()

if __name__ == "__main__":
    main()