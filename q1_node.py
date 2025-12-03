"""
Q1 - Cyclic (Round-Robin) Queue and Distribution Node
Distributes requests cyclically to P11, P12, P13
"""

import socket
import threading
import logging
from typing import List
from common import Request, send_message, receive_message, Statistics
from config import HOST, PORTS


class Q1Node:
    def __init__(self):
        self.node_name = "Q1"
        self.port = PORTS['Q1']
        
        # Service devices to distribute to
        self.service_devices = ['P11', 'P12', 'P13']
        self.current_device_index = 0  # For cyclic distribution
        
        self.running = False
        self.server_socket = None
        self.stats = Statistics(self.node_name)
        
        self.logger = logging.getLogger(self.node_name)
        
    def start(self):
        """Start Q1 node"""
        self.running = True
        self.logger.info(f"{self.node_name} starting on port {self.port}")
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, self.port))
        self.server_socket.listen(10)
        
        self.logger.info(f"{self.node_name} listening for requests...")
        
        try:
            while self.running:
                try:
                    self.server_socket.settimeout(1.0)
                    conn, addr = self.server_socket.accept()
                    threading.Thread(target=self._handle_request, args=(conn,), daemon=True).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")
        finally:
            self.stop()
            
    def _handle_request(self, conn: socket.socket):
        """Handle incoming request from clients"""
        try:
            msg = receive_message(conn)
            if not msg:
                return
            
            request = Request.from_json(msg)
            self.stats.add_request()
            
            request.add_hop(self.node_name)
            self.logger.info(f"Received {request.request_type} request {request.request_id}")
            
            # Distribute cyclically to next service device
            target_device = self._get_next_device()
            
            if self._forward_to_service(request, target_device):
                self.stats.forward_request()
                self.logger.info(f"Forwarded {request.request_id} to {target_device}")
            else:
                self.logger.error(f"Failed to forward {request.request_id} to {target_device}")
                
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
        finally:
            conn.close()
            
    def _get_next_device(self) -> str:
        """Get next device in cyclic order (Round-Robin)"""
        device = self.service_devices[self.current_device_index]
        self.current_device_index = (self.current_device_index + 1) % len(self.service_devices)
        return device
        
    def _forward_to_service(self, request: Request, device_name: str) -> bool:
        """Forward request to a service device (P11, P12, or P13)"""
        try:
            target_address = (HOST, PORTS[device_name])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(target_address)
            
            success = send_message(sock, request.to_json())
            sock.close()
            
            return success
        except Exception as e:
            self.logger.error(f"Error forwarding to {device_name}: {e}")
            return False
            
    def stop(self):
        """Stop Q1 node"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info(f"\n{self.stats}")
        

def main():
    q1 = Q1Node()
    
    try:
        q1.start()
    except KeyboardInterrupt:
        print("\nShutting down Q1...")
        q1.stop()


if __name__ == '__main__':
    main()
