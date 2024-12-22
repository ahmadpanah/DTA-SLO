from src.models.data_models import ResourceAllocation, ServiceConfig
from src.components.traffic_monitor import TrafficMonitor
from src.components.traffic_predictor import TrafficPredictor
from src.components.performance_quantifier import PerformanceImpactQuantifier
from typing import Dict, List
import pulp


class DynamicResourceAllocator:
    def __init__(self,
                 traffic_monitor: TrafficMonitor,
                 traffic_predictor: TrafficPredictor,
                 performance_quantifier: PerformanceImpactQuantifier):
        self.traffic_monitor = traffic_monitor
        self.traffic_predictor = traffic_predictor
        self.performance_quantifier = performance_quantifier
        self.current_allocations: Dict[str, ResourceAllocation] = {}
        self.min_cpu = 0.1  # Minimum CPU cores
        self.min_memory = 128  # Minimum memory in MB
        self.max_cpu = 4.0  # Maximum CPU cores
        self.max_memory = 8192  # Maximum memory in MB

    def optimize_resources(self, 
                         services: Dict[str, List[str]],  # service_id -> list of chain_ids
                         slos: Dict[str, float]  # chain_id -> latency SLO
                         ) -> Dict[str, ResourceAllocation]:
        # Create optimization problem
        problem = pulp.LpProblem("Resource_Allocation", pulp.LpMinimize)

        # Decision variables
        allocations = {}
        for service_id in services:
            allocations[service_id] = {
                'cpu': pulp.LpVariable(f"cpu_{service_id}", self.min_cpu, self.max_cpu),
                'memory': pulp.LpVariable(f"memory_{service_id}", self.min_memory, self.max_memory),
                'instances': pulp.LpVariable(f"instances_{service_id}", 1, 10, cat='Integer')
            }

        # Objective function: Minimize total resource cost
        problem += pulp.lpSum([
            allocations[service_id]['cpu'] * allocations[service_id]['instances'] * 100 +  # CPU cost weight
            allocations[service_id]['memory'] * allocations[service_id]['instances'] * 0.1  # Memory cost weight
            for service_id in services
        ])

        # Add constraints
        for service_id, chain_ids in services.items():
            # Get traffic predictions for each chain
            for chain_id in chain_ids:
                metrics = self.traffic_monitor.get_metrics(service_id, chain_id)
                if not metrics:
                    continue

                # Prepare historical data for prediction
                historical_data = np.array([[m['rps'], m['response_time'], m['error_rate']] 
                                         for m in metrics])
                predicted_load = self.traffic_predictor.predict(historical_data)[0]

                # Get performance impact analysis
                impact = self.performance_quantifier.analyze_impact(
                    service_id, chain_id, predicted_load)

                # Add SLO constraint
                problem += (
                    impact['expected_latency'] * 
                    (1.0 / allocations[service_id]['cpu']) * 
                    (1.0 / allocations[service_id]['instances']) <= 
                    slos[chain_id] * impact['risk_factor']
                )

        # Solve optimization problem
        problem.solve()

        # Extract results
        result = {}
        for service_id in services:
            result[service_id] = ResourceAllocation(
                cpu=pulp.value(allocations[service_id]['cpu']),
                memory=pulp.value(allocations[service_id]['memory']),
                instances=int(pulp.value(allocations[service_id]['instances']))
            )

        return result

    def apply_allocations(self, 
                         new_allocations: Dict[str, ResourceAllocation]) -> bool:
        """
        Apply new resource allocations to Kubernetes deployments.
        
        Args:
            new_allocations: Dictionary mapping service IDs to their new resource allocations
            
        Returns:
            bool: True if all allocations were successfully applied, False otherwise
        """
        try:
            successful_updates = []
            
            for service_id, allocation in new_allocations.items():
                try:
                    # Verify deployment exists
                    current_deployment = self._get_deployment(service_id)
                    if not current_deployment:
                        self.logger.error(f"Deployment not found for service: {service_id}")
                        continue

                    # Update deployment
                    success = self._update_kubernetes_deployment(
                        service_id=service_id,
                        cpu=allocation.cpu,
                        memory=allocation.memory,
                        instances=allocation.instances
                    )
                    
                    if success:
                        successful_updates.append(service_id)
                        self.logger.info(f"Successfully updated deployment for {service_id}")
                    else:
                        self.logger.error(f"Failed to update deployment for {service_id}")
                        
                except ApiException as api_e:
                    self.logger.error(f"Kubernetes API error for {service_id}: {str(api_e)}")
                except Exception as e:
                    self.logger.error(f"Unexpected error updating {service_id}: {str(e)}")

            # Return True only if all services were successfully updated
            return len(successful_updates) == len(new_allocations)

        except Exception as e:
            self.logger.error(f"Failed to apply allocations: {str(e)}")
            return False

    def _get_deployment(self, service_id: str) -> Optional[client.V1Deployment]:
        """
        Get current deployment for a service.
        
        Args:
            service_id: ID of the service to get deployment for
            
        Returns:
            Optional[V1Deployment]: The deployment if found, None otherwise
        """
        try:
            return self.apps_v1.read_namespaced_deployment(
                name=service_id,
                namespace=self.namespace
            )
        except ApiException as e:
            if e.status == 404:
                self.logger.warning(f"Deployment {service_id} not found")
                return None
            raise

    def _update_kubernetes_deployment(self,
                                    service_id: str,
                                    cpu: float,
                                    memory: float,
                                    instances: int) -> bool:
        """
        Update Kubernetes deployment with new resource allocation.
        
        Args:
            service_id: ID of the service to update
            cpu: CPU cores to allocate
            memory: Memory in MB to allocate
            instances: Number of replicas to run
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            # Get current deployment
            deployment = self._get_deployment(service_id)
            if not deployment:
                return False

            # Prepare resource requirements
            resources = client.V1ResourceRequirements(
                requests={
                    'cpu': str(cpu),
                    'memory': f"{int(memory)}Mi"
                },
                limits={
                    'cpu': str(cpu * 1.5),  # Set limit to 150% of request
                    'memory': f"{int(memory * 1.5)}Mi"
                }
            )

            # Update deployment spec
            deployment.spec.replicas = instances
            deployment.spec.template.spec.containers[0].resources = resources

            # Add rolling update strategy
            deployment.spec.strategy = client.V1DeploymentStrategy(
                type="RollingUpdate",
                rolling_update=client.V1RollingUpdateDeployment(
                    max_surge="25%",
                    max_unavailable="25%"
                )
            )

            # Update annotations to force update
            if not deployment.spec.template.metadata.annotations:
                deployment.spec.template.metadata.annotations = {}
            deployment.spec.template.metadata.annotations.update({
                "kubernetes.io/change-cause": f"Resource update: CPU={cpu}, Memory={memory}MB, Replicas={instances}"
            })

            # Apply the update
            self.apps_v1.patch_namespaced_deployment(
                name=service_id,
                namespace=self.namespace,
                body=deployment
            )

            # Verify the update
            return self._verify_deployment_update(
                service_id=service_id,
                expected_replicas=instances
            )

        except ApiException as e:
            self.logger.error(f"Kubernetes API error updating deployment {service_id}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error updating deployment {service_id}: {str(e)}")
            return False

    def _verify_deployment_update(self,
                                service_id: str,
                                expected_replicas: int,
                                timeout: int = 300) -> bool:
        """
        Verify that deployment update was successful.
        
        Args:
            service_id: ID of the service to verify
            expected_replicas: Expected number of replicas
            timeout: Maximum time to wait for update in seconds
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                deployment = self._get_deployment(service_id)
                if not deployment:
                    return False

                # Check if deployment is ready
                if (deployment.status.ready_replicas == expected_replicas and
                    deployment.status.updated_replicas == expected_replicas and
                    deployment.status.available_replicas == expected_replicas):
                    return True

                time.sleep(5)  # Wait before checking again
                
            except Exception as e:
                self.logger.error(f"Error verifying deployment {service_id}: {str(e)}")
                return False

        self.logger.error(f"Timeout waiting for deployment {service_id} to update")
        return False

    def get_current_allocation(self, service_id: str) -> Optional[ResourceAllocation]:
        """
        Get current resource allocation for a service.
        
        Args:
            service_id: ID of the service to get allocation for
            
        Returns:
            Optional[ResourceAllocation]: Current allocation if found, None otherwise
        """
        try:
            deployment = self._get_deployment(service_id)
            if not deployment:
                return None

            container = deployment.spec.template.spec.containers[0]
            
            # Extract CPU and memory requests
            cpu = float(container.resources.requests['cpu'])
            memory = int(container.resources.requests['memory'].rstrip('Mi'))
            instances = deployment.spec.replicas

            return ResourceAllocation(
                cpu=cpu,
                memory=memory,
                instances=instances
            )

        except Exception as e:
            self.logger.error(f"Error getting current allocation for {service_id}: {str(e)}")
            return None