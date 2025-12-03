"""
Q2x Nodes (Q21, Q22, Q23)
Queue nodes that forward requests to corresponding P2x service devices
"""

import socket
import threading
import queue
import time
import logging
from common import Request, send_message, receive_message, Statistics
from config import HOST, PORTS


class Q2xNode:
    def __init__(self, node_name: str):
        self.node_name = node_name
        self.port = PORTS[node_name]
        
        # Map to corresponding P2x service
        self.service_mapping = {
            'Q21': 'P21',
            'Q22': 'P22',
            'Q23': 'P23',
        }
        
        self.target_service = self.service_mapping[node_name]
        self.request_queue = queue.Queue()
        self.queue_entry_times = {}
        
        self.running = False
        self.server_socket = None
        self.stats = Statistics(self.node_name)
        
        self.logger = logging.getLogger(self.node_name)
        
    def start(self):
        """Start Q2x node"""
        self.running = True
        self.logger.info(f"{self.node_name} starting on port {self.port}")
        
        # Start processing thread
        processing_thread = threading.Thread(target=self._process_queue, daemon=True)
        processing_thread.start()
        
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
                    threading.Thread(target=self._handle_request, args=(conn,), daemon=True).start()
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Error accepting connection: {e}")
        finally:
            self.stop()
            
    def _handle_request(self, conn: socket.socket):
        """Handle incoming request from D"""
        try:
            msg = receive_message(conn)
            if not msg:
                return
            
            request = Request.from_json(msg)
            self.stats.add_request()
            
            request.add_hop(self.node_name)
            self.logger.info(f"Received request {request.request_id}")
            
            # Add to queue
            self.queue_entry_times[request.request_id] = time.time()
            self.request_queue.put(request)
            
            self.stats.record_queue_length(self.request_queue.qsize())
            self.logger.debug(f"Queue length: {self.request_queue.qsize()}")
                
        except Exception as e:
            self.logger.error(f"Error handling request: {e}")
        finally:
            conn.close()
            
    def _process_queue(self):
        """Process requests from queue and forward to P2x"""
        while self.running:
            try:
                request = self.request_queue.get(timeout=0.1)
                
                # Calculate wait time
                wait_time = time.time() - self.queue_entry_times.get(request.request_id, time.time())
                self.stats.process_request(wait_time)
                
                self.logger.info(f"Processing {request.request_id} (wait: {wait_time:.3f}s)")
                
                # Forward to P2x
                if self._forward_to_service(request):
                    self.stats.forward_request()
                    self.logger.info(f"Forwarded {request.request_id} to {self.target_service}")
                else:
                    self.logger.error(f"Failed to forward {request.request_id} to {self.target_service}")
                    
                # Clean up
                if request.request_id in self.queue_entry_times:
                    del self.queue_entry_times[request.request_id]
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Error processing queue: {e}")
                
    def _forward_to_service(self, request: Request) -> bool:
        """Forward request to P2x service"""
        try:
            target_address = (HOST, PORTS[self.target_service])
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)  # Timeout in case service is down
            sock.connect(target_address)
            
            success = send_message(sock, request.to_json())
            sock.close()
            
            return success
        except Exception as e:
            self.logger.warning(f"Error forwarding to {self.target_service}: {e}")
            return False
            
    def stop(self):
        """Stop Q2x node"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info(f"\n{self.stats}")


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python q2x_node.py <Q21|Q22|Q23>")
        sys.exit(1)
    
    node_name = sys.argv[1]
    if node_name not in ['Q21', 'Q22', 'Q23']:
        print("Node name must be Q21, Q22, or Q23")
        sys.exit(1)
    
    node = Q2xNode(node_name)
    
    try:
        node.start()
    except KeyboardInterrupt:
        print(f"\nShutting down {node_name}...")
        node.stop()


if __name__ == '__main__':
    main()
