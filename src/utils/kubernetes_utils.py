from kubernetes import client, config
from typing import Dict

class KubernetesManager:
    def __init__(self):
        config.load_kube_config()
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def update_deployment(self, 
                         service_id: str, 
                         cpu: float, 
                         memory: float, 
                         instances: int):
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=service_id,
                namespace="default"
            )
            
            deployment.spec.replicas = instances
            deployment.spec.template.spec.containers[0].resources = client.V1ResourceRequirements(
                requests={
                    'cpu': f'{cpu}',
                    'memory': f'{memory}Mi'
                },
                limits={
                    'cpu': f'{cpu * 1.5}',
                    'memory': f'{memory * 1.5}Mi'
                }
            )
            
            self.apps_v1.patch_namespaced_deployment(
                name=service_id,
                namespace="default",
                body=deployment
            )
            
            return True
        except Exception as e:
            print(f"Failed to update Kubernetes deployment: {str(e)}")
            return False