"""
Simple test script - Run nodes in foreground to see output
This is easier for debugging
"""

import subprocess
import time
import sys

print("="*60)
print("SIMPLE DISTRIBUTED SYSTEM TEST")
print("="*60)
print()
print("This will start nodes one-by-one in the foreground.")
print("You'll see ALL the output from each node.")
print()
print("Press Ctrl+C at any time to stop.")
print()

# Start Q1 in a new window
print("Starting Q1 in new window...")
subprocess.Popen(
    ['start', 'powershell', '-Command', f'python q1_node.py Q1'],
    shell=True
)
time.sleep(1)

# Start D
print("Starting D in new window...")
subprocess.Popen(
    ['start', 'powershell', '-Command', f'python d_node.py'],
    shell=True
)
time.sleep(1)

# Start P1x nodes
for node in ['P11', 'P12', 'P13']:
    print(f"Starting {node} in new window...")
    subprocess.Popen(
        ['start', 'powershell', '-Command', f'python p1x_service.py {node}'],
        shell=True
    )
    time.sleep(0.5)

# Start Q2x nodes
for node in ['Q21', 'Q22', 'Q23']:
    print(f"Starting {node} in new window...")
    subprocess.Popen(
        ['start', 'powershell', '-Command', f'python q2x_node.py {node}'],
        shell=True
    )
    time.sleep(0.5)

# Start P2x nodes
for node in ['P21', 'P22', 'P23']:
    print(f"Starting {node} in new window...")
    subprocess.Popen(
        ['start', 'powershell', '-Command', f'python p2x_service.py {node}'],
        shell=True
    )
    time.sleep(0.5)

print()
print("All service nodes started in separate windows!")
print("Waiting 3 seconds for initialization...")
time.sleep(3)

print()
print("Starting K1 in new window...")
subprocess.Popen(
    ['start', 'powershell', '-Command', f'python client.py K1; pause'],
    shell=True
)
time.sleep(1)

print("Starting K2 in new window...")
subprocess.Popen(
    ['start', 'powershell', '-Command', f'python client.py K2; pause'],
    shell=True
)

print()
print("="*60)
print("✓ SYSTEM RUNNING")
print("="*60)
print()
print("Check the popup windows to see node activity!")
print("Client windows will show summaries when done.")
print()
print("To stop: Close all popup windows or press Ctrl+C here")
print()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nStopping...")
