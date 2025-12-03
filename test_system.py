"""
Quick test script to verify system setup and basic functionality
"""

import socket
import time
import sys


def test_port_availability(port: int, name: str) -> bool:
    """Test if a port is available"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost', port))
        sock.close()
        print(f"✓ Port {port} ({name}) is available")
        return True
    except OSError:
        print(f"✗ Port {port} ({name}) is already in use!")
        return False


def main():
    print("="*60)
    print("DISTRIBUTED SYSTEM - PRE-FLIGHT CHECK")
    print("="*60)
    print()
    
    # Check Python version
    print("Checking Python version...")
    if sys.version_info < (3, 7):
        print(f"✗ Python 3.7+ required (found {sys.version_info.major}.{sys.version_info.minor})")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    print()
    
    # Import required modules
    print("Checking required modules...")
    required_modules = [
        'socket', 'threading', 'queue', 'time', 'random',
        'logging', 'json', 'subprocess', 'signal', 'dataclasses'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError:
            print(f"✗ {module} (missing)")
            return False
    print()
    
    # Check if required files exist
    print("Checking required files...")
    required_files = [
        'config.py',
        'common.py',
        'client.py',
        'q1_node.py',
        'p1x_service.py',
        'd_node.py',
        'q2x_node.py',
        'p2x_service.py',
        'run_system.py',
    ]
    
    import os
    all_files_exist = True
    for filename in required_files:
        if os.path.exists(filename):
            print(f"✓ {filename}")
        else:
            print(f"✗ {filename} (missing)")
            all_files_exist = False
    
    if not all_files_exist:
        return False
    print()
    
    # Check port availability
    print("Checking port availability...")
    from config import PORTS
    
    all_ports_available = True
    for node_name, port in PORTS.items():
        if not test_port_availability(port, node_name):
            all_ports_available = False
    
    if not all_ports_available:
        print()
        print("⚠️  Some ports are already in use. Please stop conflicting services.")
        return False
    
    print()
    print("="*60)
    print("✓ ALL CHECKS PASSED - SYSTEM READY TO RUN")
    print("="*60)
    print()
    print("To start the system, run:")
    print("  python run_system.py")
    print()
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
