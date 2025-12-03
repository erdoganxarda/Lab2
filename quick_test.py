"""
Quick test - Run just one client to test the system
Runs everything in the current terminal with full output
"""

import subprocess
import sys
import time
import threading

# List of all commands to run
commands = [
    ('Q1', ['python', 'q1_node.py', 'Q1']),
    ('D', ['python', 'd_node.py']),
    ('P11', ['python', 'p1x_service.py', 'P11']),
    ('P12', ['python', 'p1x_service.py', 'P12']),
    ('P13', ['python', 'p1x_service.py', 'P13']),
    ('Q21', ['python', 'q2x_node.py', 'Q21']),
    ('Q22', ['python', 'q2x_node.py', 'Q22']),
    ('Q23', ['python', 'q2x_node.py', 'Q23']),
    ('P21', ['python', 'p2x_service.py', 'P21']),
    ('P22', ['python', 'p2x_service.py', 'P22']),
    ('P23', ['python', 'p2x_service.py', 'P23']),
]

processes = []

def run_node(name, cmd):
    """Run a node and print its output"""
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    processes.append(proc)
    
    # Print output from this process
    for line in iter(proc.stdout.readline, ''):
        if line:
            print(f"[{name}] {line.rstrip()}")

print("="*70)
print("QUICK TEST - Starting all nodes with visible output")
print("="*70)
print()

# Start all service nodes in background threads
for name, cmd in commands:
    print(f"Starting {name}...")
    thread = threading.Thread(target=run_node, args=(name, cmd), daemon=True)
    thread.start()
    time.sleep(0.3)

print()
print("All service nodes started. Waiting 3 seconds...")
time.sleep(3)

print()
print("="*70)
print("Starting K1 client...")
print("="*70)
print()

# Run K1 client in foreground so we see its output and summary
try:
    proc = subprocess.Popen(
        ['python', 'client.py', 'K1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    for line in iter(proc.stdout.readline, ''):
        if line:
            print(f"[K1] {line.rstrip()}")
    
    proc.wait()
    
except KeyboardInterrupt:
    print("\n\nStopping...")

finally:
    # Clean up
    print("\nTerminating all processes...")
    for proc in processes:
        proc.terminate()
    
    print("Done!")
