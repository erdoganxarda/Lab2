"""
Dynamic Scaling Manager
Monitors queue wait times and scales P1x service instances based on demand
"""

import threading
import time
import logging
import subprocess
import sys
from typing import Dict, List
from config import SCALING_CONFIG, QUEUE_CONFIG


class ScalingManager:
    def __init__(self):
        self.running = False
        self.p1x_instances: Dict[str, List[subprocess.Popen]] = {
            'P11': [],
            'P12': [],
            'P13': []
        }
        
        # Store reference to original P1x nodes for monitoring
        self.p1x_nodes = {}
        
        self.logger = logging.getLogger("ScalingManager")
        
    def register_p1x_node(self, node_name: str, node_instance):
        """Register a P1x node for monitoring"""
        self.p1x_nodes[node_name] = node_instance
        self.logger.info(f"Registered {node_name} for monitoring")
        
    def start(self):
        """Start the scaling manager"""
        self.running = True
        self.logger.info("Scaling Manager started")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitor_and_scale, daemon=True)
        monitor_thread.start()
        
    def _monitor_and_scale(self):
        """Monitor queue wait times and scale as needed"""
        while self.running:
            time.sleep(SCALING_CONFIG['check_interval'])
            
            for node_name, node_instance in self.p1x_nodes.items():
                # Get average wait time for this node
                avg_wait_time = node_instance.stats.get_average_wait_time()
                
                # Check if scaling is needed
                if avg_wait_time > QUEUE_CONFIG['avg_wait_time_threshold'] * SCALING_CONFIG['scale_up_threshold']:
                    current_instances = len(self.p1x_instances[node_name])
                    
                    if current_instances < SCALING_CONFIG['max_instances']:
                        self._scale_up(node_name)
                    else:
                        self.logger.warning(f"{node_name} at max capacity ({current_instances} instances)")
                        
    def _scale_up(self, node_name: str):
        """Scale up a P1x service by starting additional instance"""
        current_count = len(self.p1x_instances[node_name])
        new_instance_id = current_count + 1
        
        self.logger.warning(f"⚡ SCALING UP {node_name} - Starting instance #{new_instance_id}")
        
        try:
            # Start new instance (in production, this would create a new process)
            # For this simulation, we log the action
            self.logger.info(f"✓ {node_name} instance #{new_instance_id} started successfully")
            
            # In a real implementation, you would:
            # 1. Start new process with different port
            # 2. Update Q1's routing table
            # 3. Gradually shift load to new instance
            
        except Exception as e:
            self.logger.error(f"Failed to scale up {node_name}: {e}")
            
    def stop(self):
        """Stop the scaling manager"""
        self.running = False
        
        # Clean up any additional instances
        for node_name, instances in self.p1x_instances.items():
            for proc in instances:
                try:
                    proc.terminate()
                except:
                    pass
        
        self.logger.info("Scaling Manager stopped")


class MonitoringDashboard:
    """Simple monitoring dashboard for the system"""
    
    def __init__(self):
        self.nodes = {}
        self.logger = logging.getLogger("Monitor")
        
    def register_node(self, node_name: str, node_instance):
        """Register a node for monitoring"""
        self.nodes[node_name] = node_instance
        
    def start(self):
        """Start monitoring dashboard"""
        def monitor():
            while True:
                time.sleep(10)  # Update every 10 seconds
                self._print_dashboard()
        
        threading.Thread(target=monitor, daemon=True).start()
        
    def _print_dashboard(self):
        """Print system status dashboard"""
        print("\n" + "="*80)
        print("SYSTEM MONITORING DASHBOARD")
        print("="*80)
        
        for node_name, node_instance in self.nodes.items():
            if hasattr(node_instance, 'stats'):
                stats = node_instance.stats
                print(f"\n{node_name}:")
                print(f"  Received: {stats.requests_received:4d} | "
                      f"Processed: {stats.requests_processed:4d} | "
                      f"Forwarded: {stats.requests_forwarded:4d}")
                
                if stats.requests_processed > 0:
                    print(f"  Avg Wait Time: {stats.get_average_wait_time():.3f}s | "
                          f"Avg Queue Length: {stats.get_average_queue_length():.2f}")
                    
        print("="*80 + "\n")
