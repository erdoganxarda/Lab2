"""
Main orchestrator script to start all system components
"""

import subprocess
import time
import sys
import signal
import logging
from typing import List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("Orchestrator")

# All nodes in the system
NODES = [
    # Queue and distribution nodes
    ('Q1', 'q1_node.py'),
    ('D', 'd_node.py'),
    
    # P1x service nodes
    ('P11', 'p1x_service.py'),
    ('P12', 'p1x_service.py'),
    ('P13', 'p1x_service.py'),
    
    # Q2x queue nodes
    ('Q21', 'q2x_node.py'),
    ('Q22', 'q2x_node.py'),
    ('Q23', 'q2x_node.py'),
    
    # P2x service nodes (can fail)
    ('P21', 'p2x_service.py'),
    ('P22', 'p2x_service.py'),
    ('P23', 'p2x_service.py'),
]

CLIENT_NODES = [
    ('K1', 'client.py'),
    ('K2', 'client.py'),
]

processes: List[subprocess.Popen] = []


def start_node(node_name: str, script: str) -> subprocess.Popen:
    """Start a single node"""
    logger.info(f"Starting {node_name}...")
    
    # Start the process - removed output redirection to see logs
    proc = subprocess.Popen(
        [sys.executable, script, node_name],
        text=True
    )
    
    return proc


def start_all_nodes():
    """Start all system nodes"""
    global processes
    
    logger.info("="*60)
    logger.info("STARTING DISTRIBUTED SYSTEM")
    logger.info("="*60)
    
    # Start all service and queue nodes
    for node_name, script in NODES:
        proc = start_node(node_name, script)
        processes.append(proc)
        time.sleep(0.5)  # Small delay between starts
    
    logger.info("\nAll system nodes started. Waiting for initialization...")
    time.sleep(3)  # Wait for all nodes to initialize
    
    logger.info("\n" + "="*60)
    logger.info("STARTING CLIENTS")
    logger.info("="*60)
    
    # Start clients
    for client_name, script in CLIENT_NODES:
        proc = start_node(client_name, script)
        processes.append(proc)
        time.sleep(0.5)
    
    logger.info("\nAll clients started. System is now running.")
    logger.info("\nPress Ctrl+C to stop the system.\n")


def stop_all_nodes():
    """Stop all running nodes"""
    global processes
    
    logger.info("\n" + "="*60)
    logger.info("SHUTTING DOWN DISTRIBUTED SYSTEM")
    logger.info("="*60)
    
    for proc in processes:
        try:
            proc.terminate()
        except:
            pass
    
    # Wait for processes to terminate
    time.sleep(2)
    
    # Force kill if still running
    for proc in processes:
        try:
            proc.kill()
        except:
            pass
    
    logger.info("All nodes stopped.")


def signal_handler(sig, frame):
    """Handle Ctrl+C"""
    stop_all_nodes()
    sys.exit(0)


def main():
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        start_all_nodes()
        
        # Keep main thread alive and monitor processes
        while True:
            time.sleep(1)
            
            # Check if any critical process died
            for i, proc in enumerate(processes[:len(NODES)]):  # Only check service nodes
                if proc.poll() is not None:
                    logger.error(f"A critical node has died! Exit code: {proc.returncode}")
                    
    except KeyboardInterrupt:
        pass
    finally:
        stop_all_nodes()


if __name__ == '__main__':
    main()
