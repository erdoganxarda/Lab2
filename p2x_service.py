"""
P2x Service Nodes (P21, P22, P23)
Final service devices that can fail and return responses to clients
"""

import socket
import threading
import time
import random
import logging
from common import Request, Response, send_message, receive_message, Statistics
from config import HOST, PORTS, SERVICE_TIME, P2X_FAILURE_CONFIG


class P2xServiceNode:
    def __init__(self, node_name: str):
        self.node_name = node_name
        self.port = PORTS[node_name]
        
        self.running = False
        self.is_available = True  # Can simulate failures
        self.server_socket = None
        self.stats = Statistics(self.node_name)
        
        self.logger = logging.getLogger(self.node_name)
        
    def start(self):
        """Start P2x service node"""
        self.running = True
        self.logger.info(f"{self.node_name} starting on port {self.port}")
        
        # Start failure simulation thread
        failure_thread = threading.Thread(target=self._simulate_failures, daemon=True)
        failure_thread.start()
        
        # Start server
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
                    
                    # Only accept if available
                    if self.is_available:
                        threading.Thread(target=self._handle_request, args=(conn,), daemon=True).start()
                    else:
                        self.logger.warning(f"Rejecting request - {self.node_name} is DOWN")
                        conn.close()
                        
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")
        finally:
            self.stop()
            
    def _handle_request(self, conn: socket.socket):
        """Handle incoming request from Q2x"""
        try:
            msg = receive_message(conn)
            if not msg:
                return
            
            request = Request.from_json(msg)
            self.stats.add_request()
            
            request.add_hop(self.node_name)
            self.logger.info(f"Received request {request.request_id}")
            
            # Simulate processing time
            service_time = random.uniform(
                SERVICE_TIME[self.node_name]['min'],
                SERVICE_TIME[self.node_name]['max']
            )
            time.sleep(service_time)
            
            self.stats.process_request(0)  # No queue wait time at this level
            self.logger.info(f"Processed {request.request_id} (service: {service_time:.3f}s)")
            
            # Create response
            response = Response(
                request_id=request.request_id,
                request_type=request.request_type,
                client_id=request.client_id,
                processed_by=request.hops + [self.node_name],
                timestamp=time.time(),
                success=self.is_available
            )
            
            # Send response back to client
            if self._send_response_to_client(response):
                self.stats.forward_request()
                self.logger.info(f"Sent response for {request.request_id} to {request.client_id}")
            else:
                self.logger.error(f"Failed to send response for {request.request_id}")
                
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
        finally:
            conn.close()
            
    def _send_response_to_client(self, response: Response) -> bool:
        """Send response back to the client"""
        try:
            client_address = (HOST, PORTS[response.client_id])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(client_address)
            
            success = send_message(sock, response.to_json())
            sock.close()
            
            return success
        except Exception as e:
            self.logger.error(f"Error sending response to {response.client_id}: {e}")
            return False
            
    def _simulate_failures(self):
        """Simulate random failures of the service node"""
        while self.running:
            time.sleep(P2X_FAILURE_CONFIG['check_interval'])
            
            # Random chance of failure
            if random.random() < P2X_FAILURE_CONFIG['failure_probability']:
                if self.is_available:
                    self.is_available = False
                    failure_duration = random.uniform(
                        P2X_FAILURE_CONFIG['failure_duration'][0],
                        P2X_FAILURE_CONFIG['failure_duration'][1]
                    )
                    self.logger.warning(f"⚠️  {self.node_name} GOING DOWN for {failure_duration:.1f}s")
                    
                    # Schedule recovery
                    def recover():
                        time.sleep(failure_duration)
                        self.is_available = True
                        self.logger.info(f"✓ {self.node_name} RECOVERED and back online")
                    
                    threading.Thread(target=recover, daemon=True).start()
                    
    def stop(self):
        """Stop P2x service node"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info(f"\n{self.stats}")


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python p2x_service.py <P21|P22|P23>")
        sys.exit(1)
    
    node_name = sys.argv[1]
    if node_name not in ['P21', 'P22', 'P23']:
        print("Node name must be P21, P22, or P23")
        sys.exit(1)
    
    node = P2xServiceNode(node_name)
    
    try:
        node.start()
    except KeyboardInterrupt:
        print(f"\nShutting down {node_name}...")
        node.stop()


if __name__ == '__main__':
    main()
